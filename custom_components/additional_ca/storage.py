"""Python Class for Additional CA data storage."""

from homeassistant.helpers.storage import Store

STORAGE_KEY = "additional_ca"
STORAGE_VERSION = 1


class AdditionalCAStore:
    def __init__(self, hass) -> None:
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    async def load_storage_data(self):
        return await self._store.async_load()

    async def save_storage_data(self, data):
        return await self._store.async_save(data)
