"""Privacy-safe diagnostics."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_GATEWAY_TOKEN,
    CONF_WEBHOOK_ID,
    DATA_COORDINATOR,
    DOMAIN,
)

REDACT = {
    CONF_ACCESS_TOKEN,
    CONF_GATEWAY_TOKEN,
    CONF_WEBHOOK_ID,
    "latitude",
    "longitude",
    "lat",
    "lon",
    "gps_location",
    "payload_b64",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    return {
        "entry": async_redact_data(dict(entry.data), REDACT),
        "available": coordinator.telemetry_available,
        "compact": async_redact_data(
            dict(coordinator.data.get("summary", {})), REDACT
        ),
        "protocol_schema": (
            coordinator.last_message.schema if coordinator.last_message else None
        ),
        "last_message_id": (
            coordinator.last_message.message_id if coordinator.last_message else None
        ),
        "connection_mode": coordinator.connection_mode,
        "active_transport": coordinator.active_transport,
        "last_transport_error": coordinator.last_transport_error,
    }
