"""The Config Flow for Additional CA integration."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import FileSelector, FileSelectorConfig
from homeassistant.util import slugify

from .const import (
    CONF_CAS,
    CONF_CERTIFICATE,
    CONF_DELETE,
    CONF_ENABLED,
    CONF_FILE,
    CONF_SOURCE,
    CONFIG_SUBDIR,
    DOMAIN,
    SOURCE_UI,
    SOURCE_YAML,
    UI_CA_EXTENSION,
    UI_CA_SUBDIR,
)
from .exceptions import SerialNumberException
from .utils import get_serial_number_from_cert


class AdditionalCaFlow(ConfigFlow, domain=DOMAIN):
    """Config flow of the integration, there can be only one entry."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AdditionalCaOptionsFlow:
        """Return the options flow used to manage the CAs."""
        return AdditionalCaOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Create the entry from the UI."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Additional CA", data={}, options={CONF_CAS: {}})

        return self.async_show_form(step_id="user")

    async def async_step_import(self, import_config: dict[str, Any] | None) -> ConfigFlowResult:
        """Create the entry from YAML, CAs from YAML are merged into it at setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="Additional CA", data={}, options={CONF_CAS: {}})


class InvalidCertificate(Exception):
    """The uploaded file is not a usable PEM certificate."""


class AdditionalCaOptionsFlow(OptionsFlow):
    """Add, enable/disable and delete CAs from the UI."""

    def _get_cas(self) -> dict[str, dict[str, Any]]:
        return {name: dict(ca) for name, ca in self.config_entry.options.get(CONF_CAS, {}).items()}

    def _save(self, cas: dict[str, dict[str, Any]]) -> ConfigFlowResult:
        return self.async_create_entry(data={**self.config_entry.options, CONF_CAS: cas})

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show the list of CAs and the available actions."""
        cas = self._get_cas()

        lines = []
        for name, ca in cas.items():
            state = "enabled" if ca.get(CONF_ENABLED, True) else "disabled"
            origin = "configuration.yaml" if ca.get(CONF_SOURCE) == SOURCE_YAML else "UI"
            lines.append(f"- **{name}** ({ca[CONF_FILE]}): {state}, from {origin}")

        menu = ["add"]
        if cas:
            menu.append("toggle")
        if any(ca.get(CONF_SOURCE) == SOURCE_UI for ca in cas.values()):
            menu.append("delete")

        return self.async_show_menu(
            step_id="init",
            menu_options=menu,
            description_placeholders={"cas": "\n".join(lines) or "No CA yet."},
        )

    async def async_step_add(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Add a CA from an uploaded certificate file."""
        errors: dict[str, str] = {}

        if user_input is not None:
            cas = self._get_cas()
            name = slugify(user_input[CONF_NAME])
            if not name:
                errors[CONF_NAME] = "invalid_name"
            elif name in cas:
                errors[CONF_NAME] = "already_exists"
            else:
                relative_file = f"{UI_CA_SUBDIR}/{name}{UI_CA_EXTENSION}"
                try:
                    await self._async_store_certificate(user_input[CONF_CERTIFICATE], relative_file)
                except InvalidCertificate:
                    errors[CONF_CERTIFICATE] = "invalid_certificate"
                except OSError:
                    errors["base"] = "cannot_write"
                else:
                    cas[name] = {CONF_FILE: relative_file, CONF_ENABLED: True, CONF_SOURCE: SOURCE_UI}
                    return self._save(cas)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_CERTIFICATE): FileSelector(
                    FileSelectorConfig(accept=".crt,.pem,.cer,.cert")
                ),
            }
        )
        return self.async_show_form(
            step_id="add",
            data_schema=self.add_suggested_values_to_schema(schema, user_input and {CONF_NAME: user_input[CONF_NAME]}),
            errors=errors,
        )

    async def async_step_toggle(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose which CAs are enabled, the others are disabled."""
        cas = self._get_cas()

        if user_input is not None:
            selected = user_input.get(CONF_ENABLED, [])
            for name, ca in cas.items():
                ca[CONF_ENABLED] = name in selected
            return self._save(cas)

        choices = {
            name: f"{name} ({ca[CONF_FILE]})" + (" [YAML]" if ca.get(CONF_SOURCE) == SOURCE_YAML else "")
            for name, ca in cas.items()
        }
        enabled = [name for name, ca in cas.items() if ca.get(CONF_ENABLED, True)]
        return self.async_show_form(
            step_id="toggle",
            data_schema=vol.Schema({vol.Required(CONF_ENABLED, default=enabled): cv.multi_select(choices)}),
        )

    async def async_step_delete(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Delete CAs added from the UI, CAs from YAML must be removed from configuration.yaml."""
        cas = self._get_cas()
        ui_cas = {name: ca for name, ca in cas.items() if ca.get(CONF_SOURCE) == SOURCE_UI}

        if user_input is not None:
            for name in user_input.get(CONF_DELETE, []):
                if name not in ui_cas:
                    continue
                await self.hass.async_add_executor_job(
                    _remove_ui_file, self.hass, ui_cas[name][CONF_FILE]
                )
                del cas[name]
            return self._save(cas)

        choices = {name: f"{name} ({ca[CONF_FILE]})" for name, ca in ui_cas.items()}
        return self.async_show_form(
            step_id="delete",
            data_schema=vol.Schema({vol.Required(CONF_DELETE, default=[]): cv.multi_select(choices)}),
        )

    async def _async_store_certificate(self, file_id: str, relative_file: str) -> None:
        """Copy the uploaded file into the CA folder and check it is a valid certificate.

        :raises InvalidCertificate: if the file is not a PEM certificate
        :raises OSError: if the file cannot be written
        """

        destination = Path(self.hass.config.path(CONFIG_SUBDIR), relative_file)
        await self.hass.async_add_executor_job(_copy_upload, self.hass, file_id, destination)

        try:
            await get_serial_number_from_cert(self.hass, destination)
        except SerialNumberException as err:
            await self.hass.async_add_executor_job(lambda: destination.unlink(missing_ok=True))
            raise InvalidCertificate from err


def _copy_upload(hass: HomeAssistant, file_id: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with process_uploaded_file(hass, file_id) as uploaded:
        shutil.copyfile(uploaded, destination)


def _remove_ui_file(hass: HomeAssistant, relative_file: str) -> None:
    """Delete a certificate file stored by the UI, never anything outside its folder."""
    ui_dir = Path(hass.config.path(CONFIG_SUBDIR, UI_CA_SUBDIR)).resolve()
    cert = Path(hass.config.path(CONFIG_SUBDIR), relative_file).resolve()
    if cert.is_relative_to(ui_dir):
        cert.unlink(missing_ok=True)
