"""The Config Flow for Additional CA integration."""

from homeassistant import config_entries
from .const import DOMAIN

class AdditionalCaFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_import(self, import_config):
        """Import existing YAML config."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title="Additional CA",
            data=import_config or {}
        )
