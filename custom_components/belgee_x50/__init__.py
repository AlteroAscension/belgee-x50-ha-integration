"""Belgee X50 Home Assistant integration."""

from __future__ import annotations

from typing import Any

from aiohttp import web
from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_INSTALLATION_ID,
    CONF_PUBLIC_BASE_URL,
    CONF_STALE_AFTER,
    CONF_WEBHOOK_ID,
    DATA_COORDINATOR,
    DATA_PAIRING_MANAGER,
    DATA_WEBHOOK_URL,
    DEFAULT_STALE_AFTER,
    DOMAIN,
    EVENT_ROUTE_SNAPSHOT,
    EVENT_TELEMETRY,
)
from .coordinator import X50Coordinator
from .models import normalize_message
from .pairing import PairingManager
from .pairing_http import X50PairingClaimView, X50PairingStatusView

PLATFORM_TYPES = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Register the global short-lived pairing endpoints once."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if DATA_PAIRING_MANAGER not in domain_data:
        domain_data[DATA_PAIRING_MANAGER] = PairingManager()
        hass.http.register_view(X50PairingClaimView)
        hass.http.register_view(X50PairingStatusView)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured vehicle installation."""
    stale_after = int(entry.options.get(CONF_STALE_AFTER, DEFAULT_STALE_AFTER))
    coordinator = X50Coordinator(hass, entry, stale_after)
    await coordinator.async_config_entry_first_refresh()

    webhook_id = entry.data[CONF_WEBHOOK_ID]
    token = entry.data[CONF_ACCESS_TOKEN]
    installation_id = entry.data[CONF_INSTALLATION_ID]

    async def handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: Any
    ) -> Any:
        supplied = request.headers.get("Authorization", "")
        if supplied != f"Bearer {token}":
            return web.Response(status=401, text="unauthorized")
        try:
            raw = await request.json()
            message = normalize_message(raw, installation_id)
        except (ValueError, TypeError):
            return web.Response(status=400, text="invalid payload")
        if message.installation_id != installation_id:
            return web.Response(status=403, text="installation mismatch")
        accepted = coordinator.async_ingest(message)
        if not accepted:
            return web.Response(status=202, text="ignored in gateway mode")
        hass.bus.async_fire(
            EVENT_TELEMETRY,
            {
                "entry_id": entry.entry_id,
                "installation_id": installation_id,
                "message_id": message.message_id,
                "device_kind": message.device_kind,
                "sample_time_ms": message.sample_time_ms,
                "compact": coordinator.data["summary"],
            },
        )
        if message.route_snapshot is not None:
            hass.bus.async_fire(
                EVENT_ROUTE_SNAPSHOT,
                {
                    "entry_id": entry.entry_id,
                    "installation_id": installation_id,
                    "device_kind": message.device_kind,
                    **message.route_snapshot,
                },
            )
        return web.Response(status=202, text="accepted")

    webhook.async_register(
        hass,
        DOMAIN,
        "Belgee X50 Relay",
        webhook_id,
        handle_webhook,
        allowed_methods=("POST",),
        local_only=False,
    )
    base_url = entry.options.get(
        CONF_PUBLIC_BASE_URL, entry.data.get(CONF_PUBLIC_BASE_URL)
    )
    if not base_url:
        # Compatibility with entries created by the initial preview.
        base_url = get_url(hass, prefer_external=True)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_WEBHOOK_URL: f"{base_url}/api/webhook/{webhook_id}",
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORM_TYPES)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration and its private webhook."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORM_TYPES)
    if unloaded:
        webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
