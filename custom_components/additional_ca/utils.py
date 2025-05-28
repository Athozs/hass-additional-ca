"""Python functions for Additional CA."""

import logging
import random
import shutil
import string
import subprocess
from pathlib import Path

import aiofiles
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.util.ssl import client_context

from .const import CA_SYSPATH, NEEDS_RESTART_NOTIF_ID, UPDATE_CA_SYSCMD, UPDATE_CA_SYSCMD_OPTIONS

_LOGGER = logging.getLogger(__name__)


def remove_additional_ca(ca_filename: str) -> None:
    ca_file = Path(CA_SYSPATH, ca_filename)
    try:
        ca_file.unlink
    except Exception as err:
        _LOGGER.error(f"Unable to remove CA file '{ca_file}': {str(err)}")
        raise


async def remove_all_additional_ca(hass: HomeAssistant, additional_ca_store: dict) -> None:
    """
    Removes current user's additional CA.
    Does not remove CA cert file not owned by user, in case third party wants to add its own certs they are left untouched.
    Compares CA_SYSPATH content with data stored in .storage (see homeassistant.helpers.storage)
    """
    # create a list of filenames contained in CA_SYSPATH
    ca_files = [ca.name for ca in await hass.async_add_executor_job(Path(CA_SYSPATH).iterdir)]
    _LOGGER.info(f"Current additional CA: {ca_files}")
    for ca_file in ca_files:
        for _, ca_filename in additional_ca_store.items():
            if ca_file == ca_filename:
                remove_additional_ca(ca_file)


async def copy_ca_to_system(hass: HomeAssistant, ca_src_path: Path) -> str:
    unique_ca_name = f"{generate_uid()}_{ca_src_path.name}"
    try:
        await hass.async_add_executor_job(shutil.copy, ca_src_path, Path(CA_SYSPATH, unique_ca_name))
    except Exception as err:
        _LOGGER.error(f"Unable to copy CA file '{ca_src_path.name}' to system CA: {str(err)}")
        raise
    return unique_ca_name


def update_system_ca() -> None:
    cmd = [UPDATE_CA_SYSCMD, UPDATE_CA_SYSCMD_OPTIONS]
    try:
        # status = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        status = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as err:
        _LOGGER.error(f"'{UPDATE_CA_SYSCMD}' process returned an error -> {str(err)}")
        raise
    except Exception as err:
        _LOGGER.error(f"Unable to update system CA: {str(err)}")
        raise

    if status.stderr and "Skipping duplicate certificate" not in status.stderr.decode():
        raise Exception(f"'{UPDATE_CA_SYSCMD}' status returned an error -> {status.stderr.decode().rstrip()}")


async def check_ssl_context(hass: HomeAssistant, ca_files: dict[str, str]) -> None:
    certs = client_context().get_ca_certs()

    for ca_file, common_name in ca_files.items():
        # commonName is stored in nested tuples in SSLContext
        contains_custom_ca = any(cert.get("issuer")[0][0][1] == common_name for cert in certs)
        if not contains_custom_ca:
            msg = f"CA '{ca_file}' with issuer common name '{common_name}' is missing in SSL Context. Home Assistant needs to be restarted."
            _LOGGER.error(msg)
            persistent_notification.async_create(hass, message=msg, title="Additional CA (custom integration)", notification_id=NEEDS_RESTART_NOTIF_ID)
        else:
            for cert in certs:
                if common_name in cert.get("issuer")[0][0][1]:
                    _LOGGER.info(f"Found CA with issuer common name '{common_name}'.")
                    persistent_notification.async_dismiss(hass, NEEDS_RESTART_NOTIF_ID)


async def get_issuer_common_name(cert_file: Path) -> str:
    async with aiofiles.open(cert_file, "rb") as cf:
        cert_data = await cf.read()

    common_name = None
    try:
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        issuer = cert.issuer
    except ValueError:
        _LOGGER.warning(f"The file '{cert_file.name}' appears to be an invalid TLS/SSL certificate.")
    except Exception:
        _LOGGER.error(f"Could not get issuer common name from '{cert_file.name}'.")
        raise
    else:
        for attribute in issuer:
            if attribute.oid == x509.NameOID.COMMON_NAME:
                common_name = attribute.value
                break

    return common_name


def generate_uid(length: int = 8) -> str:
    letters = string.digits
    return "".join(random.choice(letters) for _ in range(length))
