import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import ssl
from subprocess import CalledProcessError
from custom_components.additional_ca import utils
from custom_components.additional_ca.const import CA_SYSPATH, NEEDS_RESTART_NOTIF_ID, UPDATE_CA_SYSCMD, UPDATE_CA_SYSCMD_OPTIONS

class TestRemoveAdditionalCa:
    @patch('custom_components.additional_ca.utils.Path')
    def test_remove_additional_ca_success(self, mock_path):
        """Test successful CA file removal."""
        mock_file = Mock()
        mock_path.return_value = mock_file

        utils.remove_additional_ca("test_ca.crt")

        mock_path.assert_called_once_with(CA_SYSPATH, "test_ca.crt")
        mock_file.unlink.assert_called_once()

    @patch('custom_components.additional_ca.utils.Path')
    @patch('custom_components.additional_ca.utils.log')
    def test_remove_additional_ca_error(self, mock_log, mock_path):
        """Test CA file removal with error."""
        mock_file = Mock()
        mock_file.unlink.side_effect = FileNotFoundError("File not found")
        mock_path.return_value = mock_file

        with pytest.raises(FileNotFoundError):
            utils.remove_additional_ca("test_ca.crt")

        mock_log.error.assert_called_once()


class TestRemoveAllAdditionalCa:
    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.remove_additional_ca')
    @patch('custom_components.additional_ca.utils.Path')
    async def test_remove_all_additional_ca_success(self, mock_path, mock_remove):
        """Test removing all additional CA files."""
        mock_hass = AsyncMock()
        mock_file1 = Mock()
        mock_file1.name = "12345678_ca1.crt"
        mock_file2 = Mock()
        mock_file2.name = "87654321_ca2.crt"
        mock_file3 = Mock()
        mock_file3.name = "other_ca.crt"

        mock_path.return_value.iterdir.return_value = [mock_file1, mock_file2, mock_file3]
        mock_hass.async_add_executor_job.return_value = [mock_file1, mock_file2, mock_file3]

        additional_ca_store = {
            "ca1": "12345678_ca1.crt",
            "ca2": "87654321_ca2.crt"
        }

        await utils.remove_all_additional_ca(mock_hass, additional_ca_store)

        assert mock_remove.call_count == 2
        mock_remove.assert_any_call("12345678_ca1.crt")
        mock_remove.assert_any_call("87654321_ca2.crt")

    @pytest.mark.asyncio
    async def test_remove_all_additional_ca_empty_store(self):
        """Test removing CA files with empty store."""
        mock_hass = AsyncMock()
        mock_hass.async_add_executor_job.return_value = []

        await utils.remove_all_additional_ca(mock_hass, {})

        mock_hass.async_add_executor_job.assert_called_once()


class TestCopyCAToSystem:
    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.generate_uid')
    @patch('custom_components.additional_ca.utils.shutil')
    @patch('custom_components.additional_ca.utils.Path')
    async def test_copy_ca_to_system_success(self, mock_path, mock_shutil, mock_generate_uid):
        """Test successful CA file copy."""
        mock_hass = AsyncMock()
        mock_generate_uid.return_value = "12345678"
        ca_src_path = Mock()
        ca_src_path.name = "test_ca.crt"

        result = await utils.copy_ca_to_system(mock_hass, ca_src_path)

        assert result == "12345678_test_ca.crt"
        mock_hass.async_add_executor_job.assert_called_once()

    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.generate_uid')
    @patch('custom_components.additional_ca.utils.log')
    async def test_copy_ca_to_system_error(self, mock_log, mock_generate_uid):
        """Test CA file copy with error."""
        mock_hass = AsyncMock()
        mock_hass.async_add_executor_job.side_effect = OSError("Permission denied")
        mock_generate_uid.return_value = "12345678"
        ca_src_path = Mock()
        ca_src_path.name = "test_ca.crt"

        with pytest.raises(OSError):
            await utils.copy_ca_to_system(mock_hass, ca_src_path)

        mock_log.error.assert_called_once()


class TestUpdateSystemCA:
    @patch('custom_components.additional_ca.utils.subprocess.run')
    def test_update_system_ca_success(self, mock_run):
        """Test successful system CA update."""
        mock_result = Mock()
        mock_result.stderr = None
        mock_run.return_value = mock_result

        utils.update_system_ca()

        mock_run.assert_called_once_with(
            [UPDATE_CA_SYSCMD, UPDATE_CA_SYSCMD_OPTIONS],
            capture_output=True,
            check=True
        )

    @patch('custom_components.additional_ca.utils.subprocess.run')
    def test_update_system_ca_duplicate_warning(self, mock_run):
        """Test system CA update with duplicate certificate warning."""
        mock_result = Mock()
        mock_result.stderr.decode.return_value = "Skipping duplicate certificate warning"
        mock_run.return_value = mock_result

        utils.update_system_ca()

        mock_run.assert_called_once()

    @patch('custom_components.additional_ca.utils.subprocess.run')
    @patch('custom_components.additional_ca.utils.log')
    def test_update_system_ca_process_error(self, mock_log, mock_run):
        """Test system CA update with subprocess error."""
        mock_run.side_effect = CalledProcessError(1, "cmd")

        with pytest.raises(CalledProcessError):
            utils.update_system_ca()

        mock_log.error.assert_called_once()

    @patch('custom_components.additional_ca.utils.subprocess.run')
    def test_update_system_ca_stderr_error(self, mock_run):
        """Test system CA update with stderr error."""
        mock_result = Mock()
        mock_result.stderr.decode.return_value = "Some error message"
        mock_run.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            utils.update_system_ca()

        assert "status returned an error" in str(exc_info.value)


class TestCheckSSLContextByIssuerCN:
    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.client_context')
    @patch('custom_components.additional_ca.utils.persistent_notification')
    async def test_check_ssl_context_ca_found(self, mock_notification, mock_client_context):
        """Test SSL context check when CA is found."""
        mock_hass = Mock()
        mock_ssl_context = Mock()
        mock_ssl_context.get_ca_certs.return_value = [{"issuer": "Test CA"}]
        mock_client_context.return_value = mock_ssl_context

        ca_files = {"test_ca.crt": "Test CA"}

        await utils.check_ssl_context_by_issuer_cn(mock_hass, ca_files)

        mock_notification.async_dismiss.assert_called_once_with(
            mock_hass, f"Test CA_{NEEDS_RESTART_NOTIF_ID}"
        )

    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.client_context')
    @patch('custom_components.additional_ca.utils.persistent_notification')
    async def test_check_ssl_context_ca_missing(self, mock_notification, mock_client_context):
        """Test SSL context check when CA is missing."""
        mock_hass = Mock()
        mock_ssl_context = Mock()
        mock_ssl_context.get_ca_certs.return_value = [{"issuer": "Other CA"}]
        mock_client_context.return_value = mock_ssl_context

        ca_files = {"test_ca.crt": "Missing CA"}

        await utils.check_ssl_context_by_issuer_cn(mock_hass, ca_files)

        mock_notification.async_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_ssl_context_empty_common_name(self):
        """Test SSL context check with empty common name."""
        mock_hass = Mock()
        ca_files = {"test_ca.crt": ""}

        # Should not raise any exception
        await utils.check_ssl_context_by_issuer_cn(mock_hass, ca_files)


class TestCheckSSLContextBySerialNumber:
    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.client_context')
    @patch('custom_components.additional_ca.utils.persistent_notification')
    async def test_check_ssl_context_serial_found(self, mock_notification, mock_client_context):
        """Test SSL context check when serial number is found."""
        mock_hass = Mock()
        mock_ssl_context = Mock()
        mock_ssl_context.get_ca_certs.return_value = [{"serialNumber": "123456"}]
        mock_client_context.return_value = mock_ssl_context

        ca_files = {"test_ca.crt": "123456"}

        await utils.check_ssl_context_by_serial_number(mock_hass, ca_files)

        mock_notification.async_dismiss.assert_called_once_with(
            mock_hass, f"123456_{NEEDS_RESTART_NOTIF_ID}"
        )

    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.client_context')
    @patch('custom_components.additional_ca.utils.persistent_notification')
    async def test_check_ssl_context_serial_missing(self, mock_notification, mock_client_context):
        """Test SSL context check when serial number is missing."""
        mock_hass = Mock()
        mock_ssl_context = Mock()
        mock_ssl_context.get_ca_certs.return_value = [{"serialNumber": "999999"}]
        mock_client_context.return_value = mock_ssl_context

        ca_files = {"test_ca.crt": "123456"}

        await utils.check_ssl_context_by_serial_number(mock_hass, ca_files)

        mock_notification.async_create.assert_called_once()


class TestGetIssuerCommonName:
    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.aiofiles.open')
    @patch('custom_components.additional_ca.utils.x509')
    async def test_get_issuer_common_name_success(self, mock_x509, mock_aiofiles_open):
        """Test successful extraction of issuer common name."""
        mock_cert_data = b"cert_data"
        mock_file = AsyncMock()
        mock_file.read.return_value = mock_cert_data
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        mock_cert = Mock()
        mock_attribute = Mock()
        mock_attribute.oid = mock_x509.NameOID.COMMON_NAME
        mock_attribute.value = "Test CA"
        mock_cert.issuer = [mock_attribute]
        mock_x509.load_pem_x509_certificate.return_value = mock_cert

        cert_file = Path("test_ca.crt")
        result = await utils.get_issuer_common_name("test_id", cert_file)

        assert result == "Test CA"

    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.aiofiles.open')
    @patch('custom_components.additional_ca.utils.x509')
    @patch('custom_components.additional_ca.utils.log')
    async def test_get_issuer_common_name_error(self, mock_log, mock_x509, mock_aiofiles_open):
        """Test issuer common name extraction with error."""
        mock_cert_data = b"invalid_cert_data"
        mock_file = AsyncMock()
        mock_file.read.return_value = mock_cert_data
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        mock_x509.load_pem_x509_certificate.side_effect = Exception("Invalid certificate")

        cert_file = Path("test_ca.crt")
        result = await utils.get_issuer_common_name("test_id", cert_file)

        assert result is None
        mock_log.warning.assert_called_once()


class TestGetSerialNumberFromCert:
    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.ssl.SSLContext')
    async def test_get_serial_number_success(self, mock_ssl_context):
        """Test successful extraction of serial number."""
        mock_hass = AsyncMock()
        mock_ctx = Mock()
        mock_ctx.get_ca_certs.return_value = [{"serialNumber": "123456789"}]
        mock_ssl_context.return_value = mock_ctx

        cert_file = Path("test_ca.crt")
        result = await utils.get_serial_number_from_cert(mock_hass, "test_id", cert_file)

        assert result == "123456789"
        assert mock_hass.async_add_executor_job.call_count == 2

    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.ssl.SSLContext')
    @patch('custom_components.additional_ca.utils.log')
    async def test_get_serial_number_ssl_error(self, mock_log, mock_ssl_context):
        """Test serial number extraction with SSL error."""
        mock_hass = AsyncMock()
        mock_hass.async_add_executor_job.side_effect = ssl.SSLError("Invalid certificate")
        mock_ssl_context.return_value = Mock()

        cert_file = Path("test_ca.crt")
        result = await utils.get_serial_number_from_cert(mock_hass, "test_id", cert_file)

        assert result is None
        mock_log.warning.assert_called_once()

    @pytest.mark.asyncio
    @patch('custom_components.additional_ca.utils.ssl.SSLContext')
    @patch('custom_components.additional_ca.utils.log')
    async def test_get_serial_number_general_error(self, mock_log, mock_ssl_context):
        """Test serial number extraction with general error."""
        mock_hass = AsyncMock()
        mock_hass.async_add_executor_job.side_effect = Exception("General error")
        mock_ssl_context.return_value = Mock()

        cert_file = Path("test_ca.crt")

        with pytest.raises(Exception):
            await utils.get_serial_number_from_cert(mock_hass, "test_id", cert_file)

        mock_log.error.assert_called_once()


class TestGenerateUID:
    @patch('custom_components.additional_ca.utils.random.choice')
    def test_generate_uid_default_length(self, mock_choice):
        """Test UID generation with default length."""
        mock_choice.side_effect = ["1", "2", "3", "4", "5", "6", "7", "8"]

        result = utils.generate_uid()

        assert result == "12345678"
        assert len(result) == 8

    @patch('custom_components.additional_ca.utils.random.choice')
    def test_generate_uid_custom_length(self, mock_choice):
        """Test UID generation with custom length."""
        mock_choice.side_effect = ["1", "2", "3", "4"]

        result = utils.generate_uid(4)

        assert result == "1234"
        assert len(result) == 4

    def test_generate_uid_only_digits(self):
        """Test that UID contains only digits."""
        result = utils.generate_uid()

        assert result.isdigit()
        assert len(result) == 8
