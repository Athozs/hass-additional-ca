"""The Additional CA integration."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import aiofiles
import certifi
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.system_info import async_get_system_info
from homeassistant.helpers.typing import ConfigType

from .const import CONFIG_SUBDIR, DOMAIN, CERTIFI_BACKUP_PATH
from .storage import AdditionalCAStore
from .utils import (
    copy_ca_to_system,
    remove_additional_ca,
    remove_all_additional_ca,
    update_system_ca,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: {cv.string: cv.string}}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Additional CA component."""

    config_path = hass.config.path(CONFIG_SUBDIR)
    ha_sys_info = await async_get_system_info(hass)

    if not os.path.isdir(config_path):
        _LOGGER.warning(f"Folder {CONFIG_SUBDIR} not found in configuration folder.")
        return False

    try:
        store = AdditionalCAStore(hass)
        await update_ca_certificates(hass, config, store)
    except:
        _LOGGER.warning("Additional CA setup has been interrupted.")
        raise

    ha_type = ha_sys_info["installation_type"]

    if "Operating System" in ha_type or "Home Assistant OS" in ha_type or "Supervised" in ha_type:
        _LOGGER.info(f"Installation type = {ha_type}")
        try:
            await update_certifi_certificates(hass, config)
        except:
            _LOGGER.warning("Additional CA (Certifi) setup has been interrupted.")
            raise

    return True


async def update_ca_certificates(hass: HomeAssistant, config: ConfigType, store: AdditionalCAStore) -> bool:
    """Update CA certificates at system level."""

    conf = config.get(DOMAIN)

    config_path = hass.config.path(CONFIG_SUBDIR)

    try:
        os.path.isdir(config_path)
    except:
        _LOGGER.warning(f"Folder {CONFIG_SUBDIR} not found in configuration folder.")
        raise

    additional_ca_data = await store.load_storage_data()

    if additional_ca_data is None:
        additional_ca_data = {}

    # clean user's current additional CA
    try:
        remove_all_additional_ca(additional_ca_data)
    except:
        raise

    # reset system CA
    try:
        update_system_ca()
    except:
        raise

    _LOGGER.info("System CA ready.")

    # copy custom additional CA to system
    new_additional_ca_data = {}
    for ca_idname, ca_filepath in conf.items():
        additional_ca_fullpath = os.path.join(config_path, ca_filepath)

        # TODO: add certificate format checking

        if not os.path.exists(additional_ca_fullpath):
            _LOGGER.warning(f"{ca_idname}: {ca_filepath} not found.")
            continue

        if os.path.isfile(additional_ca_fullpath):
            ca_uname = await copy_ca_to_system(hass, additional_ca_fullpath)
            try:
                update_system_ca()
            except:
                _LOGGER.warning(f"Unable to load {ca_idname} ({ca_filepath}) into system CA. See previous errors.")
                remove_additional_ca(ca_uname)
                update_system_ca()
            else:
                # store CA infos for persistence across reboots in /config/.storage/
                new_additional_ca_data[ca_idname] = ca_uname
                await store.save_storage_data(new_additional_ca_data)
                _LOGGER.info(f"{ca_idname} ({ca_filepath}) -> loaded.")

        elif os.path.isdir(additional_ca_fullpath):
            _LOGGER.warning(f"{additional_ca_fullpath} is not a CA file.")

    return True


async def update_certifi_certificates(hass: HomeAssistant, config: ConfigType) -> bool:
    """Update CA certificates in Certifi bundle."""

    conf = config.get(DOMAIN)

    config_path = hass.config.path(CONFIG_SUBDIR)

    try:
        os.path.isdir(config_path)
    except:
        _LOGGER.warning(f"Folder {CONFIG_SUBDIR} not found in configuration folder.")
        raise

    certifi_bundle_path = certifi.where()
    _LOGGER.debug(f"Certifi CA bundle path: {certifi_bundle_path}")

    certifi_bundle_name = Path(certifi_bundle_path).name
    certifi_backup = Path(CERTIFI_BACKUP_PATH, certifi_bundle_name)

    if certifi_backup.exists():
        # reset Certifi bundle
        await hass.async_add_executor_job(shutil.copyfile, certifi_backup, certifi_bundle_path)
    else:
        # backup Certifi bundle
        Path(CERTIFI_BACKUP_PATH).mkdir(parents=True, exist_ok=True)
        await hass.async_add_executor_job(shutil.copyfile, certifi_bundle_path, certifi_backup)

    _LOGGER.info("Certifi bundle CA ready.")

    try:
        async with aiofiles.open(certifi_bundle_path, "r") as f:
            cacerts = await f.read()
    except:
        _LOGGER.warning(f"Unable to read {certifi_bundle_path}.")
        raise

    for ca_idname, ca_filepath in conf.items():
        additional_ca_fullpath = os.path.join(config_path, ca_filepath)

        if not os.path.exists(additional_ca_fullpath):
            _LOGGER.warning(f"{ca_idname}: {ca_filepath} not found.")
            continue

        if os.path.isfile(additional_ca_fullpath):
            async with aiofiles.open(additional_ca_fullpath, "r") as f:
                cert = await f.read()

            # Check if the private cert is present in CA bundle
            # Note: any Byte changes in source file will trigger a warning 're-add dup' (no harm)

            if cert not in cacerts:

                # original CA bundle can be fetched from upstream:
                # https://raw.githubusercontent.com/certifi/python-certifi/master/certifi/cacert.pem

                async with aiofiles.open(certifi_bundle_path, "a") as cafile:
                    await cafile.write("\n")
                    await cafile.write(f"# {DOMAIN}: {ca_idname}\n")
                    await cafile.write(cert)

                _LOGGER.info(f"{ca_idname} ({ca_filepath}) -> loaded into Certifi CA bundle.")

        elif os.path.isdir(additional_ca_fullpath):
            _LOGGER.warning(f"{additional_ca_fullpath} is not a CA file.")

    return True
