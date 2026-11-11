"""Unit tests for __init__.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.additional_ca import update_ca_certificates
from custom_components.additional_ca.const import DOMAIN


class TestUpdateCaCertificates:
    """Test cases for update_ca_certificates function."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("config", [{}, {DOMAIN: {}}, {DOMAIN: {"force_additional_ca": True}}])
    @patch("custom_components.additional_ca.update_system_ca")
    @patch("custom_components.additional_ca.remove_unused_certs", new_callable=AsyncMock)
    async def test_no_ca_left_rebuilds_system_ca(self, mock_remove, mock_update, config):
        """Removing every CA must still rebuild the system CA bundle."""
        hass = MagicMock(spec=HomeAssistant)
        hass.config = MagicMock()
        hass.config.path.return_value = "/config/additional_ca"
        mock_remove.return_value = True

        result = await update_ca_certificates(hass, config)

        assert result == {}
        mock_remove.assert_awaited_once_with(hass, {})
        mock_update.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.additional_ca.update_system_ca")
    @patch("custom_components.additional_ca.remove_unused_certs", new_callable=AsyncMock)
    async def test_nothing_removed_does_not_rebuild_system_ca(self, mock_remove, mock_update):
        """System CA bundle is not rebuilt when nothing was removed and no CA is configured."""
        hass = MagicMock(spec=HomeAssistant)
        hass.config = MagicMock()
        hass.config.path.return_value = "/config/additional_ca"
        mock_remove.return_value = False

        result = await update_ca_certificates(hass, {DOMAIN: {}})

        assert result == {}
        mock_update.assert_not_called()
