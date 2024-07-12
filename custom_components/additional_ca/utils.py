"""Python functions for Additional CA."""

import logging
import os
import random
import shutil
import string
import subprocess

from homeassistant.core import HomeAssistant

from .const import CA_SYSPATH, UPDATE_CA_SYSCMD

_LOGGER = logging.getLogger(__name__)


def remove_additional_ca(ca_filename: str) -> bool:
    os.remove(os.path.join(CA_SYSPATH, ca_filename))
    return True


async def remove_all_additional_ca(hass: HomeAssistant, additional_ca_store: dict) -> bool:
    """
    Removes current user's additional CA.
    Does not remove CA cert file not owned by user, in case third party wants to add its own certs they are left untouched.
    Compares CA_SYSPATH content with data stored in .storage (see homeassistant.helpers.storage)
    """
    ca_files_list = await hass.async_add_executor_job(os.listdir, CA_SYSPATH)
    for filename in ca_files_list:
        for _, cafile in additional_ca_store.items():
            if filename == cafile:
                file_path = os.path.join(CA_SYSPATH, filename)
                try:
                    os.unlink(file_path)
                except Exception as err:
                    _LOGGER.warning(f"Failed to delete {file_path} Reason: {err}")
                    return False
    return True


async def copy_ca_to_system(hass: HomeAssistant, ca_src_fullpath: str) -> str:
    ca_file = os.path.basename(ca_src_fullpath)
    unique_ca_name = f"{generate_uid()}_{ca_file}"
    await hass.async_add_executor_job(shutil.copy, ca_src_fullpath, os.path.join(CA_SYSPATH, unique_ca_name))
    return unique_ca_name


def update_system_ca() -> bool:
    cmd = [UPDATE_CA_SYSCMD]
    error_prefix = f"'{UPDATE_CA_SYSCMD}' returned an error -> "
    try:
        # status = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        status = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as err:
        _LOGGER.warning(f"{error_prefix}{str(err)}")
        raise
    except Exception as err:
        _LOGGER.warning(f"{error_prefix}{str(err)}")
        raise

    if status.stderr:
        _LOGGER.warning(f"{error_prefix}{status.stderr.decode().rstrip()}")
        raise Exception

    return True


def generate_uid(length: int = 8) -> str:
    letters = string.digits
    return "".join(random.choice(letters) for _ in range(length))
