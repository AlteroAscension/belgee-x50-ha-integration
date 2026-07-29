"""UI setup for Belgee X50."""

from __future__ import annotations

from typing import Any
import secrets
import uuid

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_INSTALLATION_ID,
    CONF_NAME,
    CONF_PUBLIC_BASE_URL,
    CONF_STALE_AFTER,
    CONF_WEBHOOK_ID,
    DEFAULT_NAME,
    DEFAULT_STALE_AFTER,
    DOMAIN,
    MAX_STALE_AFTER,
    MIN_STALE_AFTER,
)
from .urls import normalize_public_base_url


class X50ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create one Belgee X50 installation."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                public_base_url = normalize_public_base_url(
                    user_input[CONF_PUBLIC_BASE_URL]
                )
            except ValueError:
                errors[CONF_PUBLIC_BASE_URL] = "invalid_public_url"
            else:
                installation_id = user_input[CONF_INSTALLATION_ID].strip()
                await self.async_set_unique_id(installation_id)
                self._abort_if_unique_id_configured()
                token = user_input.get(CONF_ACCESS_TOKEN, "").strip()
                self._pending = {
                    CONF_NAME: user_input[CONF_NAME].strip(),
                    CONF_INSTALLATION_ID: installation_id,
                    CONF_ACCESS_TOKEN: token or secrets.token_urlsafe(24),
                    CONF_WEBHOOK_ID: uuid.uuid4().hex,
                    CONF_PUBLIC_BASE_URL: public_base_url,
                }
                return await self.async_step_confirm()

        configured_external_url = getattr(self.hass.config, "external_url", None) or ""
        values = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, default=values.get(CONF_NAME, DEFAULT_NAME)
                ): str,
                vol.Required(
                    CONF_INSTALLATION_ID,
                    default=values.get(CONF_INSTALLATION_ID, "belgee-x50"),
                ): str,
                vol.Required(
                    CONF_PUBLIC_BASE_URL,
                    default=values.get(
                        CONF_PUBLIC_BASE_URL, configured_external_url
                    ),
                ): str,
                vol.Optional(
                    CONF_ACCESS_TOKEN,
                    default=values.get(CONF_ACCESS_TOKEN, ""),
                ): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        base_url = self._pending[CONF_PUBLIC_BASE_URL]
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
    """Configure the public endpoint and availability timing."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                public_base_url = normalize_public_base_url(
                    user_input[CONF_PUBLIC_BASE_URL]
                )
            except ValueError:
                errors[CONF_PUBLIC_BASE_URL] = "invalid_public_url"
            else:
                data = dict(user_input)
                data[CONF_PUBLIC_BASE_URL] = public_base_url
                return self.async_create_entry(data=data)

        values = user_input or {
            CONF_PUBLIC_BASE_URL: self.config_entry.options.get(
                CONF_PUBLIC_BASE_URL,
                self.config_entry.data.get(CONF_PUBLIC_BASE_URL, ""),
            ),
            CONF_STALE_AFTER: self.config_entry.options.get(
                CONF_STALE_AFTER, DEFAULT_STALE_AFTER
            ),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_PUBLIC_BASE_URL): str,
                        vol.Required(CONF_STALE_AFTER): vol.All(
                            vol.Coerce(int),
                            vol.Range(min=MIN_STALE_AFTER, max=MAX_STALE_AFTER),
                        )
                    }
                ),
                values,
            ),
            errors=errors,
        )
