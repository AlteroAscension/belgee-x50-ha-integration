"""UI setup for Belgee X50."""

from __future__ import annotations

from typing import Any
import secrets
import uuid

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.helpers.network import get_url

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_INSTALLATION_ID,
    CONF_NAME,
    CONF_STALE_AFTER,
    CONF_WEBHOOK_ID,
    DEFAULT_NAME,
    DEFAULT_STALE_AFTER,
    DOMAIN,
    MAX_STALE_AFTER,
    MIN_STALE_AFTER,
)


class X50ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create one Belgee X50 installation."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            installation_id = user_input[CONF_INSTALLATION_ID].strip()
            await self.async_set_unique_id(installation_id)
            self._abort_if_unique_id_configured()
            token = user_input.get(CONF_ACCESS_TOKEN, "").strip()
            self._pending = {
                CONF_NAME: user_input[CONF_NAME].strip(),
                CONF_INSTALLATION_ID: installation_id,
                CONF_ACCESS_TOKEN: token or secrets.token_urlsafe(24),
                CONF_WEBHOOK_ID: uuid.uuid4().hex,
            }
            return await self.async_step_confirm()
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_INSTALLATION_ID, default="belgee-x50"): str,
                vol.Optional(CONF_ACCESS_TOKEN, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        base_url = get_url(self.hass, prefer_external=True)
        webhook_url = f"{base_url}/api/webhook/{self._pending[CONF_WEBHOOK_ID]}"
        if user_input is not None:
            return self.async_create_entry(
                title=self._pending[CONF_NAME], data=self._pending
            )
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "webhook_url": webhook_url,
                "access_token": self._pending[CONF_ACCESS_TOKEN],
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return X50OptionsFlow()


class X50OptionsFlow(OptionsFlowWithReload):
    """Configure availability timing."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_STALE_AFTER): vol.All(
                            vol.Coerce(int),
                            vol.Range(min=MIN_STALE_AFTER, max=MAX_STALE_AFTER),
                        )
                    }
                ),
                {
                    CONF_STALE_AFTER: self.config_entry.options.get(
                        CONF_STALE_AFTER, DEFAULT_STALE_AFTER
                    )
                },
            ),
        )
