"""Python functions for Additional CA."""

import logging
import shutil
import ssl
import subprocess
from pathlib import Path

import aiofiles
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.util.ssl import client_context

from .const import (
    CA_SYSPATH,
    DOMAIN,
    NEEDS_RESTART_NOTIF_ID,
    UPDATE_CA_SYSCMD,
    UPDATE_CA_SYSCMD_OPTIONS,
)
from .exceptions import SerialNumberException

log = logging.getLogger(DOMAIN)


def remove_additional_ca(ca_filename: str) -> None:
    """Remove the specified cert file from system CA path.

    :param ca_filename: the file name of the certificate like 'ca.crt'
    :type ca_filename: str
    """

    ca_file = Path(CA_SYSPATH, ca_filename)
    try:
        ca_file.unlink()
    except Exception as err:
        log.error(f"Unable to remove CA file '{ca_file}': {str(err)}")
        raise


async def remove_unused_certs(hass: HomeAssistant, config: dict) -> None:
    """Remove unused certificates from CA_SYSPATH

    :param hass: hass object from HomeAssistant core
    :type hass: HomeAssistant
    :param config: additional_ca config
    :type config: dict
    """

    conf_ca_list = [f"{k}_{Path(v).name}" for k, v in config.items()]
    system_ca_list = [f for f in await hass.async_add_executor_job(Path(CA_SYSPATH).iterdir) if f.is_file()]

    for cert in system_ca_list:
        if cert.name not in conf_ca_list:
            log.info(f"Removing unused certificate: {cert.name}")
            try:
                cert.unlink()
            except FileNotFoundError:
                log.warning(f"Certificate file {cert.name} was already removed.")
            except PermissionError:
                log.error(f"Permission denied when removing unused certificate file: {cert.name}")
                raise
            except Exception as err:
                log.error(f"Error removing unused certificate file {cert.name}: {str(err)}")
                raise


async def copy_ca_to_system(hass: HomeAssistant, ca_name: str, ca_src_path: Path) -> str:
    """Copy cert file into system CA path with a unique name to avoid
    overriding existing CA with the same name.

    :param hass: hass object from HomeAssistant core
    :type hass: HomeAssistant
    :param ca_name: the name of the certificate
    :type ca_name: str
    :param ca_src_path: the path of the certificate file
    :type ca_src_path: Path
    :return: a unique name for the copied certificate file like myca_ca.crt
    :rtype: str
    """

    unique_ca_name = f"{ca_name}_{ca_src_path.name}"
    try:
        await hass.async_add_executor_job(shutil.copy, ca_src_path, Path(CA_SYSPATH, unique_ca_name))
    except Exception as err:
        log.error(f"Unable to copy CA file '{ca_src_path.name}' to system CA: {str(err)}")
        raise
    return unique_ca_name


def update_system_ca() -> None:
    """Update the system CA trust store by running the command update-ca-certificates.

    :raises Exception: if command update-ca-certificates returns an error
    """

    cmd = [UPDATE_CA_SYSCMD, UPDATE_CA_SYSCMD_OPTIONS]
    try:
        # status = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        status = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as err:
        log.error(f"'{UPDATE_CA_SYSCMD}' process returned an error -> {str(err)}")
        raise
    except Exception as err:
        log.error(f"Unable to update system CA: {str(err)}")
        raise

    if status.stderr and "Skipping duplicate certificate" not in status.stderr.decode():
        raise Exception(f"'{UPDATE_CA_SYSCMD}' status returned an error -> {status.stderr.decode().rstrip()}")


async def check_hass_ssl_context(hass: HomeAssistant, ca_files: dict[str, str]) -> None:
    """Check if the SSL Context of Home Assistant contains specified CA files.
    If true, logs the cert filename with its identifier (the serial number),
    if false, logs an error message and create a persistent notification in Home Assistant.
    Returns nothing.

    :param hass: hass object from HomeAssistant core
    :type hass: HomeAssistant
    :param ca_files: the CA files like {'cert name': 'cert serial number', ...}
    :type ca_files: dict[str, str]
    """

    log.info("Finally verifying SSL Context")

    for ca_filename, identifers in ca_files.items():
        log.info(f"Checking SSL Context for Additional CA: {ca_filename}")
        serial_number = identifers["serial_number"]
        common_name = identifers["common_name"]
        contains_custom_ca = await check_ssl_context_by_serial_number(ca_filename, serial_number)

        # create persistent notification if needed
        notif_id = f"{serial_number}_{NEEDS_RESTART_NOTIF_ID}"
        if contains_custom_ca:
            log.info(f"SSL Context contains CA '{ca_filename}' with Common Name '{common_name}'.")
            persistent_notification.async_dismiss(hass, notif_id)
        else:
            msg = f"CA '{ca_filename}' with Common Name '{common_name}' is missing in SSL Context. Home Assistant needs to be restarted."
            log.error(msg)
            persistent_notification.async_create(
                hass,
                message=msg,
                title="Additional CA (custom integration)",
                notification_id=notif_id
            )


async def check_ssl_context_by_serial_number(ca_filename: str, serial_number: str) -> bool:
    """Check if SSL Context of Home Assistant contains the specified serial number.

    :param ca_filename: the name of certificate file, used only for logging
    :type ca_filename: str
    :param serial_number: the serial number of certificate
    :type serial_number: str
    :return: True or False if SSL Context contains the specified serial number or not
    :rtype: bool
    """

    validate_serial_number(ca_filename, serial_number)

    certs = client_context().get_ca_certs()
    for cert in certs:
        if cert.get("serialNumber") == serial_number:
            return True
    return False


async def get_issuer_common_name(cert_path: Path) -> str:
    """Get the issuer common name from a certificate.

    :param cert_path: the path of the certificate file
    :type cert_path: Path
    :return: the issuer common name
    :rtype: str
    """

    async with aiofiles.open(cert_path, "rb") as cf:
        cert_data = await cf.read()

    common_name = None
    try:
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        issuer = cert.issuer
    except Exception:
        log.warning(f"Could not get Issuer Common Name from CA '{cert_path.name}'.")
    else:
        for attribute in issuer:
            if attribute.oid == x509.NameOID.COMMON_NAME:
                common_name = attribute.value
                break

    return common_name


async def get_serial_number_from_cert(hass: HomeAssistant, cert_path: Path) -> str:
    """Get and log the serial number of a certificate.

    :param hass: hass object from HomeAssistant core
    :type hass: HomeAssistant
    :param cert_path: the path of the certificate file
    :type cert_path: Path
    :return: the serial number of the certificate
    :rtype: str
    """

    serial_number = None
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        await hass.async_add_executor_job(ctx.load_verify_locations, cert_path)
        await hass.async_add_executor_job(ctx.load_default_certs)
        ca_certs = ctx.get_ca_certs()
        if ca_certs:
            cert = ca_certs[0]
            serial_number = cert.get("serialNumber")
    except ssl.SSLError:
        log.warning(f"The file '{cert_path.name}' appears to be an invalid TLS/SSL certificate.")
    except Exception:
        log.error(f"Could not get Serial Number from '{cert_path.name}'.")
        raise

    validate_serial_number(cert_path.name, serial_number)

    return serial_number


def validate_serial_number(ca_filename: str, serial_number: str):
    """Validate a serial number.

    :param ca_filename: the name of certificate file
    :type ca_filename: str
    :param serial_number: the serial number of certificate
    :type serial_number: str
    :raises SerialNumberException: if serial number is None
    :raises SerialNumberException: if serial number is empty string
    """

    if serial_number is None:
        msg = f"The Serial Number of CA '{ca_filename}' is 'None'."
        log.error(msg)
        raise SerialNumberException(msg)
    if serial_number == "":
        msg = f"The Serial Number of CA '{ca_filename}' is empty."
        log.error(msg)
        raise SerialNumberException(msg)
