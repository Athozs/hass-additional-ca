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
    check_ssl_context_by_serial_number,
    copy_ca_to_system,
    get_issuer_common_name,
    get_serial_number_from_cert,
    log,
    remove_additional_ca,
    update_system_ca,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional("force_additional_ca", default=False): cv.string,
            },
            extra=vol.ALLOW_EXTRA,
        )
    },
    extra=vol.ALLOW_EXTRA,
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

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from a config entry."""

    config_path = Path(hass.config.path(CONFIG_SUBDIR))

    if not config_path.exists():
        log.error(f"Folder '{CONFIG_SUBDIR}' not found in configuration folder.")
        return False
    if not config_path.is_dir():
        log.error(f"'{CONFIG_SUBDIR}' must be a directory.")
        return False

    # Store entry data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    # Create a config dict in the expected format
    config = {DOMAIN: entry.data}

    try:
        ca_files = await update_ca_certificates(hass, config)
    except Exception:
        log.error("Additional CA setup has been interrupted.")
        raise

    # TODO: update docs in README.md -> certifi bundle is not updated anymore, we use certifi-linux python package instead

    # finally verifying the SSL context of Home Assistant
    try:
        await check_hass_ssl_context(hass, ca_files)
    except Exception:
        log.error("Could not check SSL Context.")
        raise

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
    :return: a dict like {'cert filename': 'cert identifier'}
    :rtype: dict[str, str]
    """

    conf = dict(config.get(DOMAIN))
    config_path = Path(hass.config.path(CONFIG_SUBDIR))
    force_additional_ca = conf.pop(FORCE_ADDITIONAL_CA, False)

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
            identifier = await get_serial_number_from_cert(hass, additional_ca_fullpath)
        except SerialNumberException:
            # let's process the next custom CA if CA does not contain a serial number
            continue
        except Exception:
            log.error(f"Could not check SSL Context for CA: {ca_key} ({ca_value}).")
            raise

        log.info(f"{ca_key} ({ca_value}) Serial Number: {identifier}")

        log.info(f"Checking presence of {ca_key} ({ca_value}) Serial Number '{identifier}' in SSL Context ")
        # check presence of CA in Home Assistant SSL Context
        ca_already_loaded = await check_ssl_context_by_serial_number(ca_value, identifier)

        # add CA to be checked in the global SSL Context at the end
        ca_files_dict[ca_value] = identifier

        # TODO: update docs in README.md -> there is a new option for user to force the load of additional CAs
        if force_additional_ca:
            log.info(f"Forcing load of {ca_key} ({ca_value}).")
        elif ca_already_loaded:
            log.info(f"{ca_key} ({ca_value}) -> already loaded.")
            # process the next custom CA
            continue

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
