"""The Additional CA integration."""

from __future__ import annotations

import logging
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
from .utils import check_ssl_context_by_issuer_cn, check_ssl_context_by_sn, copy_ca_to_system, get_issuer_common_name, get_serial_number_from_cert, remove_additional_ca, remove_all_additional_ca, update_system_ca

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: {cv.string: cv.string}}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Additional CA component."""

    config_path = Path(hass.config.path(CONFIG_SUBDIR))
    ha_sys_info = await async_get_system_info(hass)

    if not config_path.is_dir():
        _LOGGER.error(f"Folder '{CONFIG_SUBDIR}' not found in configuration folder.")
        return False

    try:
        store = AdditionalCAStore(hass)
        ca_files = await update_ca_certificates(hass, config, store)
    except Exception:
        _LOGGER.error("Additional CA setup has been interrupted.")
        raise

    ha_type = ha_sys_info["installation_type"]

    if "Operating System" in ha_type or "Home Assistant OS" in ha_type or "Supervised" in ha_type:
        _LOGGER.info(f"Installation type = {ha_type}")
        try:
            await update_certifi_certificates(hass, config)
        except Exception:
            _LOGGER.error("Additional CA (Certifi) setup has been interrupted.")
            raise

    try:
        await check_ssl_context_by_issuer_cn(hass, ca_files)
        # await check_ssl_context_by_sn(hass, ca_files)
    except Exception:
        _LOGGER.error("Could not check SSL context.")
        raise

    return True


async def update_ca_certificates(hass: HomeAssistant, config: ConfigType, store: AdditionalCAStore) -> dict[str, str]:
    """Update CA certificates at system level.
    Returns a dict like {ca_filename: issuer_common_name}.
    """

    conf = config.get(DOMAIN)

    config_path = Path(hass.config.path(CONFIG_SUBDIR))

    if not config_path.exists():
        raise Exception(f"Folder '{CONFIG_SUBDIR}' not found in configuration folder.")
    elif not config_path.is_dir():
        raise Exception(f"'{CONFIG_SUBDIR}' must be a directory.")

    additional_ca_data = await store.load_storage_data()

    if additional_ca_data is None:
        additional_ca_data = {}

    # clean user's current additional CA
    await remove_all_additional_ca(hass, additional_ca_data)

    # reset system CA
    update_system_ca()

    _LOGGER.info("System CA ready.")

    # copy custom additional CA to system
    new_additional_ca_data = {}
    ca_files_dict = {}
    for ca_key, ca_value in conf.items():
        additional_ca_fullpath = Path(config_path, ca_value)

        if not additional_ca_fullpath.exists():
            _LOGGER.warning(f"{ca_key}: {ca_value} not found.")
            continue
        elif not additional_ca_fullpath.is_file():
            _LOGGER.warning(f"'{additional_ca_fullpath}' is not a file.")
            continue

        identifier = await get_issuer_common_name(additional_ca_fullpath)
        # identifier = await get_serial_number_from_cert(additional_ca_fullpath)
        if identifier is None:
            continue

        _LOGGER.info(f"{ca_value} identifier: '{identifier}'")
        ca_files_dict[ca_value] = identifier

        ca_id = await copy_ca_to_system(hass, additional_ca_fullpath)
        try:
            update_system_ca()
        except Exception:
            _LOGGER.error(f"Unable to load CA '{ca_value}'.")
            remove_additional_ca(ca_id)
            update_system_ca()
            raise
        else:
            # store CA infos for persistence across reboots in /config/.storage/
            new_additional_ca_data[ca_key] = ca_id
            await store.save_storage_data(new_additional_ca_data)
            _LOGGER.info(f"{ca_key} ({ca_value}) -> loaded.")

    return ca_files_dict


async def update_certifi_certificates(hass: HomeAssistant, config: ConfigType) -> None:
    """Update CA certificates in Certifi bundle."""

    conf = config.get(DOMAIN)

    config_path = Path(hass.config.path(CONFIG_SUBDIR))

    if not config_path.exists():
        raise Exception(f"Folder '{CONFIG_SUBDIR}' not found in configuration folder.")
    elif not config_path.is_dir():
        raise Exception(f"'{CONFIG_SUBDIR}' must be a directory.")

    # original Certifi CA bundle is available at:
    # https://raw.githubusercontent.com/certifi/python-certifi/master/certifi/cacert.pem

    certifi_bundle_path = Path(certifi.where())
    _LOGGER.debug(f"Certifi CA bundle path: {certifi_bundle_path}")

    certifi_bundle_name = certifi_bundle_path.name
    certifi_backup = Path(CERTIFI_BACKUP_PATH, certifi_bundle_name)

    if certifi_backup.exists():
        # reset Certifi bundle
        await hass.async_add_executor_job(shutil.copyfile, certifi_backup, certifi_bundle_path)
    else:
        # backup Certifi bundle
        Path(CERTIFI_BACKUP_PATH).mkdir(parents=True, exist_ok=True)
        await hass.async_add_executor_job(shutil.copyfile, certifi_bundle_path, certifi_backup)

    _LOGGER.info("Certifi CA bundle ready.")

    try:
        async with aiofiles.open(certifi_bundle_path, "r") as f:
            certifi_bundle = await f.read()
    except Exception:
        _LOGGER.warning(f"Unable to read '{certifi_bundle_path}'.")
        raise

    for ca_key, ca_value in conf.items():
        additional_ca_fullpath = Path(config_path, ca_value)

        if not additional_ca_fullpath.exists():
            _LOGGER.warning(f"{ca_key}: {ca_value} not found.")
            continue
        elif not additional_ca_fullpath.is_file():
            _LOGGER.warning(f"'{additional_ca_fullpath}' is not a file.")
            continue

        identifier = await get_issuer_common_name(additional_ca_fullpath)
        # identifier = await get_serial_number_from_cert(additional_ca_fullpath)
        if identifier is None:
            continue

        async with aiofiles.open(additional_ca_fullpath, "r") as f:
            cert = await f.read()

        # Check if the private cert is present in CA bundle
        # Note: any Byte changes in source file will trigger a warning 're-add dup' (no harm)
        if cert not in certifi_bundle:
            async with aiofiles.open(certifi_bundle_path, "a") as cafile:
                await cafile.write("\n")
                await cafile.write(f"# {DOMAIN}: {ca_key}\n")
                await cafile.write(cert)
            _LOGGER.info(f"{ca_key} ({ca_value}) -> loaded into Certifi CA bundle.")
