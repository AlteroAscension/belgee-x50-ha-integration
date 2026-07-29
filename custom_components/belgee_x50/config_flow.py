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
    CONF_CONNECTION_MODE,
    CONF_GATEWAY_POLL_SECONDS,
    CONF_GATEWAY_ACCESS_TOKEN,
    CONF_GATEWAY_TOKEN,
    CONF_GATEWAY_URL,
    CONF_INSTALLATION_ID,
    CONF_NAME,
    CONF_PAIRING_DEVICE,
    CONF_PUBLIC_BASE_URL,
    CONF_START_PAIRING,
    CONF_STALE_AFTER,
    CONF_WEBHOOK_ID,
    CONNECTION_AUTO,
    CONNECTION_GATEWAY,
    CONNECTION_GATEWAY_POLL,
    CONNECTION_GATEWAY_PUSH,
    CONNECTION_MODES,
    CONNECTION_RELAY,
    DATA_PAIRING_MANAGER,
    DEFAULT_NAME,
    DEFAULT_GATEWAY_POLL_SECONDS,
    DEFAULT_STALE_AFTER,
    DOMAIN,
    MAX_STALE_AFTER,
    MAX_GATEWAY_POLL_SECONDS,
    MIN_STALE_AFTER,
    MIN_GATEWAY_POLL_SECONDS,
    PAIRING_DEVICE_GATEWAY,
    PAIRING_DEVICE_RELAY,
    PAIRING_DEVICES,
)
from .gateway import normalize_gateway_url
from .pairing import PairingError, PairingManager, PairingSession
from .urls import normalize_public_base_url


class X50ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create one Belgee X50 installation."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending: dict[str, Any] = {}
        self._pairing_session_id: str | None = None

    @property
    def _pairing_manager(self) -> PairingManager:
        return self.hass.data[DOMAIN][DATA_PAIRING_MANAGER]

    def _open_pairing(self) -> PairingSession:
        base_url = self._pending[CONF_PUBLIC_BASE_URL]
        pairing_device = self._pending.get(
            CONF_PAIRING_DEVICE, PAIRING_DEVICE_RELAY
        )
        token_key = (
            CONF_GATEWAY_ACCESS_TOKEN
            if pairing_device == PAIRING_DEVICE_GATEWAY
            else CONF_ACCESS_TOKEN
        )
        session = self._pairing_manager.open(
            {
                "telemetry_url": (
                    f"{base_url}/api/webhook/{self._pending[CONF_WEBHOOK_ID]}"
                ),
                "bearer_token": self._pending[token_key],
                "installation_id": self._pending[CONF_INSTALLATION_ID],
                "source_kind": pairing_device,
            }
        )
        self._pairing_session_id = session.session_id
        return session

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            mode = str(user_input.get(CONF_CONNECTION_MODE, CONNECTION_RELAY))
            public_value = str(
                user_input.get(CONF_PUBLIC_BASE_URL, "")
            ).strip()
            public_base_url = ""
            if public_value:
                try:
                    public_base_url = normalize_public_base_url(public_value)
                except ValueError:
                    errors[CONF_PUBLIC_BASE_URL] = "invalid_public_url"
            if mode in (
                CONNECTION_RELAY,
                CONNECTION_GATEWAY_PUSH,
                CONNECTION_AUTO,
            ) and not public_base_url:
                errors[CONF_PUBLIC_BASE_URL] = "public_url_required"
            gateway_value = str(user_input.get(CONF_GATEWAY_URL, "")).strip()
            gateway_url = ""
            if gateway_value:
                try:
                    gateway_url = normalize_gateway_url(gateway_value)
                except ValueError:
                    errors[CONF_GATEWAY_URL] = "invalid_gateway_url"
            if mode in (CONNECTION_GATEWAY, CONNECTION_GATEWAY_POLL) \
                    and not gateway_url:
                errors[CONF_GATEWAY_URL] = "gateway_url_required"
            if not errors:
                installation_id = user_input[CONF_INSTALLATION_ID].strip()
                pairing_device = str(
                    user_input.get(
                        CONF_PAIRING_DEVICE, PAIRING_DEVICE_RELAY
                    )
                )
                if mode == CONNECTION_RELAY:
                    pairing_device = PAIRING_DEVICE_RELAY
                elif mode == CONNECTION_GATEWAY_PUSH:
                    pairing_device = PAIRING_DEVICE_GATEWAY
                await self.async_set_unique_id(installation_id)
                self._abort_if_unique_id_configured()
                self._pending = {
                    CONF_NAME: user_input[CONF_NAME].strip(),
                    CONF_INSTALLATION_ID: installation_id,
                    CONF_ACCESS_TOKEN: secrets.token_urlsafe(24),
                    CONF_GATEWAY_ACCESS_TOKEN: secrets.token_urlsafe(24),
                    CONF_WEBHOOK_ID: uuid.uuid4().hex,
                    CONF_PUBLIC_BASE_URL: public_base_url,
                    CONF_CONNECTION_MODE: mode,
                    CONF_PAIRING_DEVICE: pairing_device,
                    CONF_GATEWAY_URL: gateway_url,
                    CONF_GATEWAY_TOKEN: str(
                        user_input.get(CONF_GATEWAY_TOKEN, "")
                    ).strip(),
                    CONF_GATEWAY_POLL_SECONDS: int(
                        user_input.get(
                            CONF_GATEWAY_POLL_SECONDS,
                            DEFAULT_GATEWAY_POLL_SECONDS,
                        )
                    ),
                }
                if mode in (
                    CONNECTION_RELAY,
                    CONNECTION_GATEWAY_PUSH,
                    CONNECTION_AUTO,
                ):
                    self._open_pairing()
                    return await self.async_step_pair()
                return self.async_create_entry(
                    title=self._pending[CONF_NAME], data=self._pending
                )

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
                vol.Optional(
                    CONF_PUBLIC_BASE_URL,
                    default=values.get(
                        CONF_PUBLIC_BASE_URL, configured_external_url
                    ),
                ): str,
                vol.Required(
                    CONF_CONNECTION_MODE,
                    default=values.get(CONF_CONNECTION_MODE, CONNECTION_RELAY),
                ): vol.In(CONNECTION_MODES),
                vol.Required(
                    CONF_PAIRING_DEVICE,
                    default=values.get(
                        CONF_PAIRING_DEVICE, PAIRING_DEVICE_RELAY
                    ),
                ): vol.In(PAIRING_DEVICES),
                vol.Optional(
                    CONF_GATEWAY_URL,
                    default=values.get(CONF_GATEWAY_URL, ""),
                ): str,
                vol.Optional(
                    CONF_GATEWAY_TOKEN,
                    default=values.get(CONF_GATEWAY_TOKEN, ""),
                ): str,
                vol.Required(
                    CONF_GATEWAY_POLL_SECONDS,
                    default=values.get(
                        CONF_GATEWAY_POLL_SECONDS,
                        DEFAULT_GATEWAY_POLL_SECONDS,
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_GATEWAY_POLL_SECONDS,
                        max=MAX_GATEWAY_POLL_SECONDS,
                    ),
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        session = (
            self._pairing_manager.get(self._pairing_session_id or "")
            if self._pairing_session_id
            else None
        )
        if session is None:
            return self.async_abort(reason="pairing_expired")
        if user_input is not None:
            if not session.claimed:
                return self.async_show_form(
                    step_id="pair",
                    data_schema=vol.Schema({}),
                    errors={"base": "relay_not_connected"},
                    description_placeholders=self._pair_placeholders(session),
                )
            return await self.async_step_pair_confirm()
        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({}),
            description_placeholders=self._pair_placeholders(session),
        )

    async def async_step_pair_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        session = self._pairing_manager.get(self._pairing_session_id or "")
        if session is None:
            return self.async_abort(reason="pairing_expired")
        if not session.claimed:
            return await self.async_step_pair()
        if user_input is not None:
            try:
                self._pairing_manager.confirm(session.session_id)
            except PairingError:
                return self.async_abort(reason="pairing_expired")
            return self.async_create_entry(
                title=self._pending[CONF_NAME],
                data=self._pending,
            )
        return self.async_show_form(
            step_id="pair_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "device_name": session.claimed_device_name or "X50 Relay",
                "relay_version": session.claimed_relay_version or "unknown",
                "fingerprint": session.fingerprint or "—",
            },
        )

    def _pair_placeholders(self, session: PairingSession) -> dict[str, str]:
        code = f"{session.code[:4]}-{session.code[4:]}"
        return {
            "pairing_code": code,
            "public_base_url": self._pending[CONF_PUBLIC_BASE_URL],
            "expires_minutes": "5",
        }

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return X50OptionsFlow()


class X50OptionsFlow(OptionsFlowWithReload):
    """Configure the public endpoint and availability timing."""

    def __init__(self) -> None:
        self._pairing_session_id: str | None = None
        self._pending_options: dict[str, Any] = {}
        self._pending_token: str | None = None
        self._pending_pairing_device = PAIRING_DEVICE_RELAY

    @property
    def _pairing_manager(self) -> PairingManager:
        return self.hass.data[DOMAIN][DATA_PAIRING_MANAGER]

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            mode = str(user_input.get(CONF_CONNECTION_MODE, CONNECTION_RELAY))
            public_value = str(
                user_input.get(CONF_PUBLIC_BASE_URL, "")
            ).strip()
            public_base_url = ""
            if public_value:
                try:
                    public_base_url = normalize_public_base_url(public_value)
                except ValueError:
                    errors[CONF_PUBLIC_BASE_URL] = "invalid_public_url"
            start_pairing_requested = bool(
                user_input.get(CONF_START_PAIRING, False)
            )
            if (mode in (CONNECTION_RELAY, CONNECTION_GATEWAY_PUSH,
                         CONNECTION_AUTO) or start_pairing_requested) \
                    and not public_base_url:
                errors[CONF_PUBLIC_BASE_URL] = "public_url_required"
            gateway_value = str(user_input.get(CONF_GATEWAY_URL, "")).strip()
            gateway_url = ""
            if gateway_value:
                try:
                    gateway_url = normalize_gateway_url(gateway_value)
                except ValueError:
                    errors[CONF_GATEWAY_URL] = "invalid_gateway_url"
            if mode in (CONNECTION_GATEWAY, CONNECTION_GATEWAY_POLL) \
                    and not gateway_url:
                errors[CONF_GATEWAY_URL] = "gateway_url_required"
            if not errors:
                data = dict(user_input)
                data[CONF_PUBLIC_BASE_URL] = public_base_url
                data[CONF_GATEWAY_URL] = gateway_url
                start_pairing = bool(data.pop(CONF_START_PAIRING, False))
                if start_pairing:
                    self._pending_options = data
                    self._pending_token = secrets.token_urlsafe(24)
                    self._pending_pairing_device = str(
                        data.pop(
                            CONF_PAIRING_DEVICE, PAIRING_DEVICE_RELAY
                        )
                    )
                    entry_data = self.config_entry.data
                    session = self._pairing_manager.open(
                        {
                            "telemetry_url": (
                                f"{public_base_url}/api/webhook/"
                                f"{entry_data[CONF_WEBHOOK_ID]}"
                            ),
                            "bearer_token": self._pending_token,
                            "installation_id": entry_data[CONF_INSTALLATION_ID],
                            "source_kind": self._pending_pairing_device,
                        }
                    )
                    self._pairing_session_id = session.session_id
                    return await self.async_step_pair()
                return self.async_create_entry(data=data)

        values = user_input or {
            CONF_PUBLIC_BASE_URL: self.config_entry.options.get(
                CONF_PUBLIC_BASE_URL,
                self.config_entry.data.get(CONF_PUBLIC_BASE_URL, ""),
            ),
            CONF_STALE_AFTER: self.config_entry.options.get(
                CONF_STALE_AFTER, DEFAULT_STALE_AFTER
            ),
            CONF_START_PAIRING: False,
            CONF_PAIRING_DEVICE: PAIRING_DEVICE_RELAY,
            CONF_CONNECTION_MODE: self.config_entry.options.get(
                CONF_CONNECTION_MODE,
                self.config_entry.data.get(CONF_CONNECTION_MODE, CONNECTION_RELAY),
            ),
            CONF_GATEWAY_URL: self.config_entry.options.get(
                CONF_GATEWAY_URL,
                self.config_entry.data.get(CONF_GATEWAY_URL, ""),
            ),
            CONF_GATEWAY_TOKEN: self.config_entry.options.get(
                CONF_GATEWAY_TOKEN,
                self.config_entry.data.get(CONF_GATEWAY_TOKEN, ""),
            ),
            CONF_GATEWAY_POLL_SECONDS: self.config_entry.options.get(
                CONF_GATEWAY_POLL_SECONDS,
                self.config_entry.data.get(
                    CONF_GATEWAY_POLL_SECONDS, DEFAULT_GATEWAY_POLL_SECONDS
                ),
            ),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Optional(CONF_PUBLIC_BASE_URL): str,
                        vol.Required(CONF_STALE_AFTER): vol.All(
                            vol.Coerce(int),
                            vol.Range(min=MIN_STALE_AFTER, max=MAX_STALE_AFTER),
                        ),
                        vol.Optional(CONF_START_PAIRING): bool,
                        vol.Required(CONF_PAIRING_DEVICE): vol.In(
                            PAIRING_DEVICES
                        ),
                        vol.Required(CONF_CONNECTION_MODE): vol.In(
                            CONNECTION_MODES
                        ),
                        vol.Optional(CONF_GATEWAY_URL): str,
                        vol.Optional(CONF_GATEWAY_TOKEN): str,
                        vol.Required(CONF_GATEWAY_POLL_SECONDS): vol.All(
                            vol.Coerce(int),
                            vol.Range(
                                min=MIN_GATEWAY_POLL_SECONDS,
                                max=MAX_GATEWAY_POLL_SECONDS,
                            ),
                        ),
                    }
                ),
                values,
            ),
            errors=errors,
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        session = self._pairing_manager.get(self._pairing_session_id or "")
        if session is None:
            return self.async_abort(reason="pairing_expired")
        placeholders = {
            "pairing_code": f"{session.code[:4]}-{session.code[4:]}",
            "public_base_url": self._pending_options[CONF_PUBLIC_BASE_URL],
            "expires_minutes": "5",
        }
        if user_input is not None:
            if not session.claimed:
                return self.async_show_form(
                    step_id="pair",
                    data_schema=vol.Schema({}),
                    errors={"base": "relay_not_connected"},
                    description_placeholders=placeholders,
                )
            return await self.async_step_pair_confirm()
        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({}),
            description_placeholders=placeholders,
        )

    async def async_step_pair_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        session = self._pairing_manager.get(self._pairing_session_id or "")
        if session is None:
            return self.async_abort(reason="pairing_expired")
        if not session.claimed:
            return await self.async_step_pair()
        if user_input is not None:
            if not self._pending_token:
                return self.async_abort(reason="pairing_expired")
            token_key = (
                CONF_GATEWAY_ACCESS_TOKEN
                if self._pending_pairing_device == PAIRING_DEVICE_GATEWAY
                else CONF_ACCESS_TOKEN
            )
            entry_data = {
                **self.config_entry.data,
                token_key: self._pending_token,
            }
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=entry_data
            )
            try:
                self._pairing_manager.confirm(session.session_id)
            except PairingError:
                return self.async_abort(reason="pairing_expired")
            return self.async_create_entry(data=self._pending_options)
        return self.async_show_form(
            step_id="pair_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "device_name": session.claimed_device_name or "X50 Relay",
                "relay_version": session.claimed_relay_version or "unknown",
                "fingerprint": session.fingerprint or "—",
            },
        )
