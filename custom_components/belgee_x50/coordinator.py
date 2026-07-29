"""Push coordinator for Belgee X50 telemetry."""

from __future__ import annotations

from datetime import timedelta
import time
from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CONNECTION_MODE,
    CONF_GATEWAY_POLL_SECONDS,
    CONF_GATEWAY_TOKEN,
    CONF_GATEWAY_URL,
    CONNECTION_AUTO,
    CONNECTION_GATEWAY,
    CONNECTION_RELAY,
    DEFAULT_GATEWAY_POLL_SECONDS,
    DOMAIN,
    EVENT_ROUTE_SNAPSHOT,
)
from .gateway import (
    gateway_headers,
    gateway_route_revision,
    gateway_route_url,
    gateway_telemetry_url,
    validate_gateway_payload,
)
from .models import NormalizedMessage, compact_summary, normalize_message


class X50Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Keep the latest compact Relay state and age it without network polling."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, stale_after: int
    ) -> None:
        self.entry = entry
        self.installation_id = entry.data["installation_id"]
        self.connection_mode = entry.options.get(
            CONF_CONNECTION_MODE,
            entry.data.get(CONF_CONNECTION_MODE, CONNECTION_RELAY),
        )
        poll_seconds = int(
            entry.options.get(
                CONF_GATEWAY_POLL_SECONDS,
                entry.data.get(
                    CONF_GATEWAY_POLL_SECONDS, DEFAULT_GATEWAY_POLL_SECONDS
                ),
            )
        )
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=(
                    poll_seconds
                    if self.connection_mode in (CONNECTION_GATEWAY, CONNECTION_AUTO)
                    else min(30, max(10, stale_after // 3))
                )
            ),
        )
        self.stale_after = stale_after
        self.last_message: NormalizedMessage | None = None
        self.last_relay_message: NormalizedMessage | None = None
        self.last_gateway_message: NormalizedMessage | None = None
        self.active_transport = "none"
        self.last_transport_error: str | None = None
        self.last_gateway_route_revision = ""
        self.async_set_updated_data({"summary": {}, "raw": {}})

    async def _async_update_data(self) -> dict[str, Any]:
        if self.connection_mode == CONNECTION_GATEWAY:
            await self._async_fetch_gateway()
        elif self.connection_mode == CONNECTION_AUTO and not self._relay_is_fresh():
            await self._async_fetch_gateway()
        return self.data

    async def _async_fetch_gateway(self) -> None:
        base_url = self.entry.options.get(
            CONF_GATEWAY_URL, self.entry.data.get(CONF_GATEWAY_URL, "")
        )
        if not base_url:
            self.last_transport_error = "gateway_url_not_configured"
            return
        token = self.entry.options.get(
            CONF_GATEWAY_TOKEN, self.entry.data.get(CONF_GATEWAY_TOKEN, "")
        )
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(
                gateway_telemetry_url(base_url),
                headers=gateway_headers(token),
                timeout=10,
            ) as response:
                response.raise_for_status()
                raw = validate_gateway_payload(await response.json())
            message = normalize_message(raw, self.installation_id)
            self.last_gateway_message = message
            self.last_transport_error = None
            self._apply(message, "gateway")
            await self._async_sync_gateway_route(session, base_url, token, raw)
        except Exception as error:  # HA reports the actionable detail in diagnostics.
            self.last_transport_error = f"{type(error).__name__}: {error}"

    async def _async_sync_gateway_route(
        self, session: Any, base_url: str, token: str, telemetry: dict[str, Any]
    ) -> None:
        revision = gateway_route_revision(telemetry)
        if revision == self.last_gateway_route_revision:
            return
        if revision == "none":
            self.last_gateway_route_revision = revision
            return
        async with session.get(
            gateway_route_url(base_url),
            headers=gateway_headers(token),
            timeout=15,
        ) as response:
            response.raise_for_status()
            route = validate_gateway_payload(await response.json())
        if not route.get("available", False):
            return
        self.last_gateway_route_revision = revision
        self.hass.bus.async_fire(
            EVENT_ROUTE_SNAPSHOT,
            {
                "entry_id": self.entry.entry_id,
                "installation_id": self.installation_id,
                "device_kind": "head_unit",
                "schema": "x50.route.v2",
                "snapshot_id": revision,
                "available": True,
                "observed_at_ms": int(time.time() * 1000),
                "route": route,
            },
        )

    def async_ingest(self, message: NormalizedMessage) -> bool:
        """Accept Relay push unless the user selected Gateway-only mode."""
        self.last_relay_message = message
        if self.connection_mode == CONNECTION_GATEWAY:
            return False
        self._apply(message, "relay")
        return True

    def _apply(self, message: NormalizedMessage, transport: str) -> None:
        self.last_message = message
        self.active_transport = transport
        summary = compact_summary(message.compact)
        summary["connection_mode"] = self.connection_mode
        summary["active_transport"] = transport
        self.async_set_updated_data(
            {"summary": summary, "raw": message.compact}
        )

    def _relay_is_fresh(self) -> bool:
        if self.last_relay_message is None:
            return False
        age = time.time() - self.last_relay_message.received_time_ms / 1000
        return age <= self.stale_after

    @property
    def telemetry_available(self) -> bool:
        if self.last_message is None:
            return False
        age = time.time() - self.last_message.received_time_ms / 1000
        return age <= self.stale_after
