"""Unit tests for utils.py module."""

import pytest
import ssl
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from homeassistant.core import HomeAssistant

from custom_components.additional_ca.utils import (
    remove_additional_ca,
    copy_ca_to_system,
    update_system_ca,
    check_hass_ssl_context,
    check_ssl_context_by_serial_number,
    get_issuer_common_name,
    get_serial_number_from_cert,
    validate_serial_number,
)
from custom_components.additional_ca.exceptions import SerialNumberException
from custom_components.additional_ca.const import (
    CA_SYSPATH,
    UPDATE_CA_SYSCMD,
    UPDATE_CA_SYSCMD_OPTIONS,
    NEEDS_RESTART_NOTIF_ID,
)


class TestRemoveAdditionalCa:
    """Test cases for remove_additional_ca function."""

    @patch("custom_components.additional_ca.utils.Path")
    def test_remove_additional_ca_success(self, mock_path):
        """Test successful removal of CA file."""
        # Arrange
        mock_ca_file = MagicMock()
        mock_path.return_value = mock_ca_file
        ca_filename = "test_ca.crt"

        # Act
        remove_additional_ca(ca_filename)

        # Assert
        mock_path.assert_called_once_with(CA_SYSPATH, ca_filename)
        mock_ca_file.unlink.assert_called_once()

    @patch("custom_components.additional_ca.utils.Path")
    @patch("custom_components.additional_ca.utils.log")
    def test_remove_additional_ca_file_not_found(self, mock_log, mock_path):
        """Test removal when file doesn't exist."""
        # Arrange
        mock_ca_file = MagicMock()
        mock_ca_file.unlink.side_effect = FileNotFoundError("File not found")
        mock_path.return_value = mock_ca_file
        ca_filename = "nonexistent.crt"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            remove_additional_ca(ca_filename)

        mock_log.error.assert_called_once()

    @patch("custom_components.additional_ca.utils.Path")
    @patch("custom_components.additional_ca.utils.log")
    def test_remove_additional_ca_permission_error(self, mock_log, mock_path):
        """Test removal with permission error."""
        # Arrange
        mock_ca_file = MagicMock()
        mock_ca_file.unlink.side_effect = PermissionError("Permission denied")
        mock_path.return_value = mock_ca_file
        ca_filename = "test_ca.crt"

        # Act & Assert
        with pytest.raises(PermissionError):
            remove_additional_ca(ca_filename)

        mock_log.error.assert_called_once()


class TestCopyCarToSystem:
    """Test cases for copy_ca_to_system function."""

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.shutil")
    @patch("custom_components.additional_ca.utils.Path")
    async def test_copy_ca_to_system_success(self, mock_path, mock_shutil):
        """Test successful copying of CA file."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        ca_name = "test_ca"
        ca_src_path = Path("/source/test_ca.crt")
        expected_unique_name = "test_ca_test_ca.crt"

        # Act
        result = await copy_ca_to_system(hass, ca_name, ca_src_path)

        # Assert
        assert result == expected_unique_name
        hass.async_add_executor_job.assert_called_once_with(
            mock_shutil.copy, ca_src_path, mock_path.return_value
        )
        mock_path.assert_called_once_with(CA_SYSPATH, expected_unique_name)

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.shutil")
    @patch("custom_components.additional_ca.utils.Path")
    @patch("custom_components.additional_ca.utils.log")
    async def test_copy_ca_to_system_failure(self, mock_log, mock_path, mock_shutil):
        """Test failure during copying of CA file."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock(side_effect=Exception("Copy failed"))
        ca_name = "test_ca"
        ca_src_path = Path("/source/test_ca.crt")

        # Act & Assert
        with pytest.raises(Exception, match="Copy failed"):
            await copy_ca_to_system(hass, ca_name, ca_src_path)

        mock_log.error.assert_called_once()


class TestUpdateSystemCa:
    """Test cases for update_system_ca function."""

    @patch("custom_components.additional_ca.utils.subprocess")
    def test_update_system_ca_success(self, mock_subprocess):
        """Test successful system CA update."""
        # Arrange
        mock_result = MagicMock()
        mock_result.stderr = b""
        mock_subprocess.run.return_value = mock_result

        # Act
        update_system_ca()

        # Assert
        expected_cmd = [UPDATE_CA_SYSCMD, UPDATE_CA_SYSCMD_OPTIONS]
        mock_subprocess.run.assert_called_once_with(
            expected_cmd, capture_output=True, check=True
        )

    @patch("custom_components.additional_ca.utils.subprocess")
    def test_update_system_ca_success_with_duplicate_warning(self, mock_subprocess):
        """Test successful system CA update with duplicate certificate warning."""
        # Arrange
        mock_result = MagicMock()
        mock_result.stderr = b"Skipping duplicate certificate something.crt"
        mock_subprocess.run.return_value = mock_result

        # Act
        update_system_ca()

        # Assert
        mock_subprocess.run.assert_called_once()

    @patch("custom_components.additional_ca.utils.subprocess.run")
    @patch("custom_components.additional_ca.utils.log")
    def test_update_system_ca_called_process_error(self, mock_log, mock_run):
        """Test system CA update with CalledProcessError."""
        # Arrange
        error = subprocess.CalledProcessError(1, "update-ca-certificates")
        mock_run.side_effect = error

        # Act & Assert
        with pytest.raises(subprocess.CalledProcessError):
            update_system_ca()

        mock_log.error.assert_called_once()

    @patch("custom_components.additional_ca.utils.subprocess.run")
    @patch("custom_components.additional_ca.utils.log")
    def test_update_system_ca_other_exception(self, mock_log, mock_run):
        """Test system CA update with other exception."""
        # Arrange
        mock_run.side_effect = OSError("Command not found")

        # Act & Assert
        with pytest.raises(OSError):
            update_system_ca()

        mock_log.error.assert_called_once()

    @patch("custom_components.additional_ca.utils.subprocess.run")
    def test_update_system_ca_stderr_error(self, mock_run):
        """Test system CA update with stderr error."""
        # Arrange
        mock_result = MagicMock()
        mock_result.stderr = b"Some error occurred"
        mock_run.return_value = mock_result

        # Act & Assert
        with pytest.raises(Exception, match="status returned an error"):
            update_system_ca()


class TestCheckHassSslContext:
    """Test cases for check_hass_ssl_context function."""

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.check_ssl_context_by_serial_number")
    @patch("custom_components.additional_ca.utils.persistent_notification")
    @patch("custom_components.additional_ca.utils.log")
    async def test_check_hass_ssl_context_ca_found(self, mock_log, mock_notification, mock_check_ssl):
        """Test SSL context check when CA is found."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        ca_files = {"test_ca.crt": {
            "serial_number": "12345678",
            "common_name": "One Common Name"
            }
        }
        mock_check_ssl.return_value = True

        # Act
        await check_hass_ssl_context(hass, ca_files)

        # Assert
        mock_check_ssl.assert_called_once_with("test_ca.crt", "12345678")
        mock_notification.async_dismiss.assert_called_once_with(
            hass, f"12345678_{NEEDS_RESTART_NOTIF_ID}"
        )
        mock_log.info.assert_any_call("Finally verifying SSL Context")
        mock_log.info.assert_any_call("Checking SSL Context for Additional CA: test_ca.crt")

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.check_ssl_context_by_serial_number")
    @patch("custom_components.additional_ca.utils.persistent_notification")
    @patch("custom_components.additional_ca.utils.log")
    async def test_check_hass_ssl_context_ca_not_found(self, mock_log, mock_notification, mock_check_ssl):
        """Test SSL context check when CA is not found."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        ca_files = {"test_ca.crt": {
            "serial_number": "12345678",
            "common_name": "One Common Name"
            }
        }
        mock_check_ssl.return_value = False

        # Act
        await check_hass_ssl_context(hass, ca_files)

        # Assert
        mock_check_ssl.assert_called_once_with("test_ca.crt", "12345678")
        mock_notification.async_create.assert_called_once_with(
            hass,
            message="CA 'test_ca.crt' with Common Name 'One Common Name' is missing in SSL Context. Home Assistant needs to be restarted.",
            title="Additional CA (custom integration)",
            notification_id=f"12345678_{NEEDS_RESTART_NOTIF_ID}"
        )
        mock_log.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.check_ssl_context_by_serial_number")
    @patch("custom_components.additional_ca.utils.persistent_notification")
    async def test_check_hass_ssl_context_multiple_cas(self, mock_notification, mock_check_ssl):
        """Test SSL context check with multiple CAs."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        ca_files = {
            "ca1.crt": {
                "serial_number": "11111111",
                "common_name": "One Common Name"
            },
            "ca2.crt": {
                "serial_number": "22222222",
                "common_name": "Another Common Name"
            },
        }
        mock_check_ssl.side_effect = [True, False]

        # Act
        await check_hass_ssl_context(hass, ca_files)

        # Assert
        assert mock_check_ssl.call_count == 2
        mock_check_ssl.assert_any_call("ca1.crt", "11111111")
        mock_check_ssl.assert_any_call("ca2.crt", "22222222")
        mock_notification.async_dismiss.assert_called_once_with(
            hass, f"11111111_{NEEDS_RESTART_NOTIF_ID}"
        )
        mock_notification.async_create.assert_called_once()


class TestCheckSslContextBySerialNumber:
    """Test cases for check_ssl_context_by_serial_number function."""

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.validate_serial_number")
    @patch("custom_components.additional_ca.utils.client_context")
    async def test_check_ssl_context_by_serial_number_found(self, mock_client_context, mock_validate):
        """Test SSL context check when serial number is found."""
        # Arrange
        mock_context = MagicMock()
        mock_context.get_ca_certs.return_value = [
            {"serialNumber": "12345678"},
            {"serialNumber": "87654321"},
        ]
        mock_client_context.return_value = mock_context
        ca_filename = "test_ca.crt"
        serial_number = "12345678"

        # Act
        result = await check_ssl_context_by_serial_number(ca_filename, serial_number)

        # Assert
        assert result is True
        mock_validate.assert_called_once_with(ca_filename, serial_number)

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.validate_serial_number")
    @patch("custom_components.additional_ca.utils.client_context")
    async def test_check_ssl_context_by_serial_number_not_found(self, mock_client_context, mock_validate):
        """Test SSL context check when serial number is not found."""
        # Arrange
        mock_context = MagicMock()
        mock_context.get_ca_certs.return_value = [
            {"serialNumber": "87654321"},
            {"serialNumber": "11111111"},
        ]
        mock_client_context.return_value = mock_context
        ca_filename = "test_ca.crt"
        serial_number = "12345678"

        # Act
        result = await check_ssl_context_by_serial_number(ca_filename, serial_number)

        # Assert
        assert result is False
        mock_validate.assert_called_once_with(ca_filename, serial_number)

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.validate_serial_number")
    @patch("custom_components.additional_ca.utils.client_context")
    async def test_check_ssl_context_by_serial_number_empty_certs(self, mock_client_context, mock_validate):
        """Test SSL context check when no certificates are found."""
        # Arrange
        mock_context = MagicMock()
        mock_context.get_ca_certs.return_value = []
        mock_client_context.return_value = mock_context
        ca_filename = "test_ca.crt"
        serial_number = "12345678"

        # Act
        result = await check_ssl_context_by_serial_number(ca_filename, serial_number)

        # Assert
        assert result is False
        mock_validate.assert_called_once_with(ca_filename, serial_number)


class TestGetIssuerCommonName:
    """Test cases for get_issuer_common_name function."""

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.aiofiles.open")
    @patch("custom_components.additional_ca.utils.x509.load_pem_x509_certificate")
    async def test_get_issuer_common_name_success(self, mock_load_cert, mock_aiofiles_open):
        """Test successful extraction of issuer common name."""
        # Arrange
        cert_path = Path("/test/cert.crt")
        cert_data = b"fake_cert_data"

        # Mock file operations
        mock_file = AsyncMock()
        mock_file.read.return_value = cert_data
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        # Mock certificate parsing
        mock_cert = MagicMock()
        mock_attr_org = MagicMock()
        mock_attr_org.oid = x509.NameOID.ORGANIZATION_NAME
        mock_attr_org.value = "Test Org"

        mock_attr_cn = MagicMock()
        mock_attr_cn.oid = x509.NameOID.COMMON_NAME
        mock_attr_cn.value = "Test CA"

        mock_cert.issuer = [mock_attr_org, mock_attr_cn]
        mock_load_cert.return_value = mock_cert

        # Act
        result = await get_issuer_common_name(cert_path)

        # Assert
        assert result == "Test CA"
        mock_aiofiles_open.assert_called_once_with(cert_path, "rb")
        mock_load_cert.assert_called_once_with(cert_data, default_backend())

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.aiofiles.open")
    @patch("custom_components.additional_ca.utils.x509.load_pem_x509_certificate")
    @patch("custom_components.additional_ca.utils.log")
    async def test_get_issuer_common_name_no_common_name(self, mock_log, mock_load_cert, mock_aiofiles_open):
        """Test when certificate has no common name."""
        # Arrange
        cert_path = Path("/test/cert.crt")
        cert_data = b"fake_cert_data"

        # Mock file operations
        mock_file = AsyncMock()
        mock_file.read.return_value = cert_data
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        # Mock certificate parsing
        mock_cert = MagicMock()
        mock_attr_org = MagicMock()
        mock_attr_org.oid = x509.NameOID.ORGANIZATION_NAME
        mock_attr_org.value = "Test Org"

        mock_cert.issuer = [mock_attr_org]
        mock_load_cert.return_value = mock_cert

        # Act
        result = await get_issuer_common_name(cert_path)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.aiofiles.open")
    @patch("custom_components.additional_ca.utils.x509.load_pem_x509_certificate")
    @patch("custom_components.additional_ca.utils.log")
    async def test_get_issuer_common_name_invalid_cert(self, mock_log, mock_load_cert, mock_aiofiles_open):
        """Test with invalid certificate data."""
        # Arrange
        cert_path = Path("/test/invalid_cert.crt")
        cert_data = b"invalid_cert_data"

        # Mock file operations
        mock_file = AsyncMock()
        mock_file.read.return_value = cert_data
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        # Mock certificate parsing error
        mock_load_cert.side_effect = Exception("Invalid certificate")

        # Act
        result = await get_issuer_common_name(cert_path)

        # Assert
        assert result is None
        mock_log.warning.assert_called_once_with(
            "Could not get Issuer Common Name from CA 'invalid_cert.crt'."
        )


class TestGetSerialNumberFromCert:
    """Test cases for get_serial_number_from_cert function."""

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.validate_serial_number")
    @patch("custom_components.additional_ca.utils.ssl.SSLContext")
    async def test_get_serial_number_from_cert_success(self, mock_ssl_context, mock_validate):
        """Test successful extraction of serial number."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        cert_path = Path("/test/cert.crt")

        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_context.get_ca_certs.return_value = [{"serialNumber": "12345678"}]

        # Act
        result = await get_serial_number_from_cert(hass, cert_path)

        # Assert
        assert result == "12345678"
        mock_ssl_context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
        assert hass.async_add_executor_job.call_count == 2
        hass.async_add_executor_job.assert_any_call(mock_context.load_verify_locations, cert_path)
        hass.async_add_executor_job.assert_any_call(mock_context.load_default_certs)
        mock_validate.assert_called_once_with("cert.crt", "12345678")

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.validate_serial_number")
    @patch("custom_components.additional_ca.utils.ssl.SSLContext")
    @patch("custom_components.additional_ca.utils.log")
    async def test_get_serial_number_from_cert_ssl_error(self, mock_log, mock_ssl_context, mock_validate):
        """Test with SSL error."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock(side_effect=ssl.SSLError("Invalid certificate"))
        cert_path = Path("/test/invalid_cert.crt")

        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context

        # Act
        result = await get_serial_number_from_cert(hass, cert_path)

        # Assert
        assert result is None
        mock_log.warning.assert_called_once_with(
            "The file 'invalid_cert.crt' appears to be an invalid TLS/SSL certificate."
        )
        # validate_serial_number is still called with None serial number
        mock_validate.assert_called_once_with('invalid_cert.crt', None)

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.validate_serial_number")
    @patch("custom_components.additional_ca.utils.ssl.SSLContext")
    @patch("custom_components.additional_ca.utils.log")
    async def test_get_serial_number_from_cert_other_exception(self, mock_log, mock_ssl_context, mock_validate):
        """Test with other exception."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock(side_effect=Exception("Unexpected error"))
        cert_path = Path("/test/cert.crt")

        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context

        # Act & Assert
        with pytest.raises(Exception, match="Unexpected error"):
            await get_serial_number_from_cert(hass, cert_path)

        mock_log.error.assert_called_once_with("Could not get Serial Number from 'cert.crt'.")
        # validate_serial_number is not called because exception is re-raised
        mock_validate.assert_not_called()

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.utils.validate_serial_number")
    @patch("custom_components.additional_ca.utils.ssl.SSLContext")
    async def test_get_serial_number_from_cert_no_certs(self, mock_ssl_context, mock_validate):
        """Test when no certificates are found."""
        # Arrange
        hass = MagicMock(spec=HomeAssistant)
        hass.async_add_executor_job = AsyncMock()
        cert_path = Path("/test/cert.crt")

        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_context.get_ca_certs.return_value = []

        # Act
        result = await get_serial_number_from_cert(hass, cert_path)

        # Assert
        assert result is None
        mock_validate.assert_called_once_with("cert.crt", None)


class TestValidateSerialNumber:
    """Test cases for validate_serial_number function."""

    def test_validate_serial_number_valid(self):
        """Test validation with valid serial number."""
        # Arrange
        ca_filename = "test_ca.crt"
        serial_number = "12345678"

        # Act & Assert (should not raise)
        validate_serial_number(ca_filename, serial_number)

    @patch("custom_components.additional_ca.utils.log")
    def test_validate_serial_number_none(self, mock_log):
        """Test validation with None serial number."""
        # Arrange
        ca_filename = "test_ca.crt"
        serial_number = None

        # Act & Assert
        with pytest.raises(SerialNumberException, match="The Serial Number of CA 'test_ca.crt' is 'None'."):
            validate_serial_number(ca_filename, serial_number)

        mock_log.error.assert_called_once_with("The Serial Number of CA 'test_ca.crt' is 'None'.")

    @patch("custom_components.additional_ca.utils.log")
    def test_validate_serial_number_empty(self, mock_log):
        """Test validation with empty serial number."""
        # Arrange
        ca_filename = "test_ca.crt"
        serial_number = ""

        # Act & Assert
        with pytest.raises(SerialNumberException, match="The Serial Number of CA 'test_ca.crt' is empty."):
            validate_serial_number(ca_filename, serial_number)

        mock_log.error.assert_called_once_with("The Serial Number of CA 'test_ca.crt' is empty.")
