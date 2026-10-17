"""The Additional CA integration."""

from __future__ import annotations

from pathlib import Path

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_CAS,
    CONF_ENABLED,
    CONF_FILE,
    CONFIG_SUBDIR,
    DATA_YAML_CONFIG,
    DOMAIN,
)
from .exceptions import SerialNumberException
from .utils import (
    check_hass_ssl_context,
    clear_restart_issues,
    copy_ca_to_system,
    get_issuer_common_name,
    get_serial_number_from_cert,
    has_system_certs,
    log,
    merge_yaml_cas,
    remove_additional_ca,
    remove_unused_certs,
    update_system_ca,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {cv.string: cv.string}
    },
    extra=vol.ALLOW_EXTRA
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Additional CA component.

    CAs declared in configuration.yaml are kept in memory here and merged into the
    config entry (which holds all the CAs, from YAML and from the UI) when it is set up.
    """

    log.info("Starting Additional CA setup")

    hass.data[DATA_YAML_CONFIG] = dict(config.get(DOMAIN) or {})

    # Create the config entry from YAML if it does not exist yet
    if DOMAIN in config and not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data={}
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""

    config_path = Path(hass.config.path(CONFIG_SUBDIR))
    await hass.async_add_executor_job(lambda: config_path.mkdir(parents=True, exist_ok=True))
    if not config_path.is_dir():
        log.error(f"'{CONFIG_SUBDIR}' must be a directory.")
        return False

    stored_cas = entry.options.get(CONF_CAS, {})
    cas = merge_yaml_cas(stored_cas, hass.data.get(DATA_YAML_CONFIG, {}))
    if cas != stored_cas:
        hass.config_entries.async_update_entry(entry, options={**entry.options, CONF_CAS: cas})

    enabled_cas = {name: ca[CONF_FILE] for name, ca in cas.items() if ca.get(CONF_ENABLED, True)}

    try:
        ca_files = await update_ca_certificates(hass, enabled_cas)
    except Exception:
        log.error("Additional CA setup has been interrupted.")
        raise

    # finally verifying the SSL context of Home Assistant
    clear_restart_issues(hass)
    try:
        await check_hass_ssl_context(hass, ca_files)
    except Exception:
        log.error("Could not check SSL Context.")
        raise

    # registered after the sync above to avoid reloading because of our own update
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Clean up on unload."""
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options are changed from the UI."""
    await hass.config_entries.async_reload(entry.entry_id)


async def update_ca_certificates(hass: HomeAssistant, conf: dict[str, str]) -> dict[str, dict[str, str]]:
    """Update system CA trust store by adding custom CA if it is not already present.

    :param hass: hass object from HomeAssistant core
    :type hass: HomeAssistant
    :param conf: the enabled CAs like {'ca name': 'cert filename relative to config/additional_ca'}
    :type conf: dict[str, str]
    :raises Exception: if unable to check SSL Context for CA
    :raises Exception: if unable to update system CA
    :return: a dict like {'cert filename': {'serial_number': ..., 'common_name': ...}}
    :rtype: dict[str, dict[str, str]]
    """

    if not conf and not await hass.async_add_executor_job(has_system_certs):
        return {}

    config_path = Path(hass.config.path(CONFIG_SUBDIR))

    await remove_unused_certs(hass, conf)

    if not conf:
        # every CA was disabled or removed, rebuild the trust store without them
        update_system_ca()
        return {}

    ca_files_dict = {}
    for ca_key, ca_value in conf.items():
        log.info(f"Processing CA: {ca_key} ({ca_value})")
        additional_ca_fullpath = Path(config_path, ca_value)

        if not additional_ca_fullpath.exists():
            log.warning(f"{ca_key}: {ca_value} not found.")
            continue
        if not additional_ca_fullpath.is_file():
            log.warning(f"'{additional_ca_fullpath}' is not a file.")
            continue

        common_name = await get_issuer_common_name(additional_ca_fullpath)
        log.info(f"{ca_key} ({ca_value}) Issuer Common Name: {common_name}")

        try:
            serial_number = await get_serial_number_from_cert(hass, additional_ca_fullpath)
        except SerialNumberException:
            # let's process the next custom CA if CA does not contain a serial number
            continue
        except Exception:
            raise

        # add CA to be checked in the global SSL Context at the end
        ca_files_dict[ca_value] = {}
        ca_files_dict[ca_value]["serial_number"] = serial_number
        ca_files_dict[ca_value]["common_name"] = common_name


        ca_id = await copy_ca_to_system(hass, ca_key, additional_ca_fullpath)
        try:
            update_system_ca()
        except Exception:
            log.error(f"Unable to load CA '{ca_value}'.")
            remove_additional_ca(ca_id)
            update_system_ca()
            raise

        log.info(f"{ca_key} ({ca_value}) -> new CA loaded.")

    return ca_files_dict
