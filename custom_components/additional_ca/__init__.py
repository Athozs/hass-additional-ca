"""The Additional CA integration."""

from __future__ import annotations

import shutil
from pathlib import Path

import aiofiles
import certifi
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.system_info import async_get_system_info
from homeassistant.helpers.typing import ConfigType

from .const import CERTIFI_BACKUP_PATH, CONFIG_SUBDIR, DOMAIN
from .storage import AdditionalCAStore
from .utils import log, check_hass_ssl_context, check_ssl_context_by_serial_number, copy_ca_to_system, get_issuer_common_name, get_serial_number_from_cert, remove_additional_ca, update_system_ca
from .exceptions import SerialNumberException


CONFIG_SCHEMA = vol.Schema({DOMAIN: {cv.string: cv.string}}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Additional CA component."""

    log.info("Starting Additional CA setup")

    config_path = Path(hass.config.path(CONFIG_SUBDIR))
    ha_sys_info = await async_get_system_info(hass)

    if not config_path.exists():
        log.error(f"Folder '{CONFIG_SUBDIR}' not found in configuration folder.")
        return False
    elif not config_path.is_dir():
        log.error(f"'{CONFIG_SUBDIR}' must be a directory.")
        return False

    try:
        store = AdditionalCAStore(hass)
        ca_files = await update_ca_certificates(hass, config, store)
    except Exception:
        log.error("Additional CA setup has been interrupted.")
        raise

    ha_type = ha_sys_info["installation_type"]

    if "Operating System" in ha_type or "Home Assistant OS" in ha_type or "Supervised" in ha_type:
        log.info(f"Installation type = {ha_type}")
        try:
            # Permanent export of environment variables in HAOS is currently unsupported;
            # therefore, the Certifi CA bundle is updated as a workaround.
            ca_files = await update_certifi_certificates(hass, config)
        except Exception:
            log.error("Additional CA (Certifi) setup has been interrupted.")
            raise

    try:
        await check_hass_ssl_context(hass, ca_files)
    except Exception:
        log.error("Could not check SSL Context.")
        raise

    return True


async def update_ca_certificates(hass: HomeAssistant, config: ConfigType, store: AdditionalCAStore) -> dict[str, str]:
    """Update system CA trust store by adding custom CA if it is not already present.

    :param hass: hass object from HomeAssistant core
    :type hass: HomeAssistant
    :param config: config object from HomeAssistant helpers
    :type config: ConfigType
    :param store: store object from AdditionalCAStore
    :type store: AdditionalCAStore
    :raises Exception: if unable to check SSL Context for CA
    :raises Exception: if unable to update system CA
    :return: a dict like {'cert filename': 'cert identifier'}
    :rtype: dict[str, str]
    """

    conf = config.get(DOMAIN)
    config_path = Path(hass.config.path(CONFIG_SUBDIR))

    ca_files_dict = {}
    for ca_key, ca_value in conf.items():
        log.info(f"Processing CA: {ca_key} ({ca_value})")
        additional_ca_fullpath = Path(config_path, ca_value)

        if not additional_ca_fullpath.exists():
            log.warning(f"{ca_key}: {ca_value} not found.")
            continue
        elif not additional_ca_fullpath.is_file():
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

        # TODO: add an option in conf for user to force CA to be copied and loaded into system CA
        if ca_already_loaded:
            log.info(f"{ca_key} ({ca_value}) -> already loaded.")
            # process the next custom CA
            continue

        ca_id = await copy_ca_to_system(hass, additional_ca_fullpath)
        try:
            update_system_ca()
        except Exception:
            log.error(f"Unable to load CA '{ca_value}'.")
            remove_additional_ca(ca_id)
            update_system_ca()
            raise
        else:
            log.info(f"{ca_key} ({ca_value}) -> new CA loaded.")

    return ca_files_dict


async def update_certifi_certificates(hass: HomeAssistant, config: ConfigType) -> dict[str, str]:
    """Update Certifi CA bundle by adding custom CA.

    :param hass: hass object from HomeAssistant core
    :type hass: HomeAssistant
    :param config: config object from HomeAssistant helpers
    :type config: ConfigType
    :raises Exception: if config/additional_ca directory is missing
    :raises Exception: if unable to load a CA
    :return: a dict like {'cert filename': 'cert identifier'}
    :rtype: dict[str, str]
    """

    conf = config.get(DOMAIN)

    config_path = Path(hass.config.path(CONFIG_SUBDIR))

    # original Certifi CA bundle is available at:
    # https://raw.githubusercontent.com/certifi/python-certifi/master/certifi/cacert.pem

    certifi_bundle_path = Path(certifi.where())
    log.debug(f"Certifi CA bundle path: {certifi_bundle_path}")

    certifi_bundle_name = certifi_bundle_path.name
    certifi_backup = Path(CERTIFI_BACKUP_PATH, certifi_bundle_name)

    if certifi_backup.exists():
        # reset Certifi bundle
        await hass.async_add_executor_job(shutil.copyfile, certifi_backup, certifi_bundle_path)
    else:
        # backup Certifi bundle
        Path(CERTIFI_BACKUP_PATH).mkdir(parents=True, exist_ok=True)
        await hass.async_add_executor_job(shutil.copyfile, certifi_bundle_path, certifi_backup)

    log.info("Certifi CA bundle ready.")

    try:
        async with aiofiles.open(certifi_bundle_path, "r") as f:
            certifi_bundle = await f.read()
    except Exception:
        log.warning(f"Unable to read '{certifi_bundle_path}'.")
        raise

    ca_files_dict = {}
    for ca_key, ca_value in conf.items():
        log.info(f"[Certifi CA bundle] Processing CA: {ca_key} ({ca_value})")
        additional_ca_fullpath = Path(config_path, ca_value)

        if not additional_ca_fullpath.exists():
            log.warning(f"[Certifi CA bundle] {ca_key}: {ca_value} not found.")
            continue
        elif not additional_ca_fullpath.is_file():
            log.warning(f"[Certifi CA bundle] '{additional_ca_fullpath}' is not a file.")
            continue

        await get_issuer_common_name(ca_key, additional_ca_fullpath)
        identifier = await get_serial_number_from_cert(hass, ca_key, additional_ca_fullpath)
        if identifier is None:
            log.warning(f"[Certifi CA bundle] CA won't be loaded: {ca_key} ({ca_value})")
            continue

        ca_files_dict[ca_value] = identifier

        async with aiofiles.open(additional_ca_fullpath, "r") as f:
            cert = await f.read()

        # Check if the private cert is present in CA bundle
        # Note: any Byte changes in source file will trigger a warning 're-add dup' (no harm)
        if cert not in certifi_bundle:
            async with aiofiles.open(certifi_bundle_path, "a") as cafile:
                await cafile.write("\n")
                await cafile.write(f"# {DOMAIN}: {ca_key}\n")
                await cafile.write(cert)
            log.info(f"{ca_key} ({ca_value}) -> loaded into Certifi CA bundle.")

    return ca_files_dict
