"""The Additional CA integration."""

from __future__ import annotations

from pathlib import Path

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CONFIG_SUBDIR, DOMAIN, FORCE_ADDITIONAL_CA
from .exceptions import SerialNumberException
from .utils import (
    check_hass_ssl_context,
    copy_ca_to_system,
    get_issuer_common_name,
    get_serial_number_from_cert,
    log,
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
    """Set up Additional CA component."""

    log.info("Starting Additional CA setup")

    # Handle YAML configuration by creating a config entry
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "import"}, data=config[DOMAIN]
            )
        )

    config_path = Path(hass.config.path(CONFIG_SUBDIR))

    if not config_path.exists():
        log.error(f"Folder '{CONFIG_SUBDIR}' not found in configuration folder.")
        return False
    if not config_path.is_dir():
        log.error(f"'{CONFIG_SUBDIR}' must be a directory.")
        return False

    try:
        ca_files = await update_ca_certificates(hass, config)
    except Exception:
        log.error("Additional CA setup has been interrupted.")
        raise

    # finally verifying the SSL context of Home Assistant
    try:
        await check_hass_ssl_context(hass, ca_files)
    except Exception:
        log.error("Could not check SSL Context.")
        raise

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from a config entry."""
    # Store entry data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Clean up on unload."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


async def update_ca_certificates(hass: HomeAssistant, config: ConfigType) -> dict[str, str]:
    """Update system CA trust store by adding custom CA if it is not already present.

    :param hass: hass object from HomeAssistant core
    :type hass: HomeAssistant
    :param config: config object from HomeAssistant helpers
    :type config: ConfigType
    :raises Exception: if unable to check SSL Context for CA
    :raises Exception: if unable to update system CA
    :return: a dict like {'cert filename': 'cert serial_number'}
    :rtype: dict[str, str]
    """

    conf = config.get(DOMAIN)
    config_path = Path(hass.config.path(CONFIG_SUBDIR))

    # Ignore deprecated option 'force_additional_ca' (boolean) from config
    conf.pop(FORCE_ADDITIONAL_CA, None)

    await remove_unused_certs(hass, conf)

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
