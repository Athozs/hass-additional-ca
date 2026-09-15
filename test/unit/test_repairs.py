"""Unit tests for repairs.py module."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.additional_ca.repairs import (
    NeedsRestartRepairFlow,
    async_create_fix_flow,
)


class TestAsyncCreateFixFlow:
    """Test cases for async_create_fix_flow function."""

    @pytest.mark.asyncio
    async def test_async_create_fix_flow_returns_flow(self):
        """Test that the factory returns a NeedsRestartRepairFlow instance."""
        hass = MagicMock()

        flow = await async_create_fix_flow(hass, "some_issue_id", None)

        assert isinstance(flow, NeedsRestartRepairFlow)


class TestNeedsRestartRepairFlow:
    """Test cases for NeedsRestartRepairFlow."""

    @pytest.mark.asyncio
    async def test_init_step_shows_confirm_step(self):
        """Test that the init step delegates to the confirm step."""
        flow = NeedsRestartRepairFlow()
        flow.hass = MagicMock()
        flow.hass.services.async_call = AsyncMock()
        # The repairs framework sets `.data` from the issue's `data` before starting the flow.
        flow.data = {"ca_filename": "test_ca.crt", "common_name": "Test CA"}

        result = await flow.async_step_init()

        assert result["type"] == "form"
        assert result["step_id"] == "confirm"
        flow.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_confirm_step_no_input_shows_form(self):
        """Test that the confirm step shows a form with the issue's placeholders."""
        flow = NeedsRestartRepairFlow()
        flow.hass = MagicMock()
        flow.hass.services.async_call = AsyncMock()
        flow.data = {"ca_filename": "test_ca.crt", "common_name": "Test CA"}

        result = await flow.async_step_confirm()

        assert result["type"] == "form"
        assert result["step_id"] == "confirm"
        assert result["description_placeholders"] == flow.data
        flow.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_confirm_step_with_input_restarts_home_assistant(self):
        """Test that submitting the confirm step triggers a HA restart."""
        flow = NeedsRestartRepairFlow()
        flow.hass = MagicMock()
        flow.hass.services.async_call = AsyncMock()
        flow.data = {"ca_filename": "test_ca.crt", "common_name": "Test CA"}

        result = await flow.async_step_confirm(user_input={})

        flow.hass.services.async_call.assert_called_once_with(
            "homeassistant", "restart", blocking=False
        )
        assert result["type"] == "create_entry"
