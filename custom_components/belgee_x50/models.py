"""Protocol normalization without Home Assistant dependencies."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import base64
import gzip
import json
import math
import time
from typing import Any


def nested(data: dict[str, Any], path: str, default: Any = None) -> Any:
    """Read a dotted path from a JSON object."""
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def finite(value: Any, default: float | None = None) -> float | None:
    """Return a finite float or the fallback."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def integer(value: Any, default: int | None = None) -> int | None:
    """Return an integer or the fallback."""
    number = finite(value)
    return int(number) if number is not None else default


def _first(data: dict[str, Any], paths: tuple[str, ...], default: Any = None) -> Any:
    for path in paths:
        value = nested(data, path)
        if value is not None:
            return value
    return default


def boolean(value: Any, default: bool | None = None) -> bool | None:
    """Interpret common protocol boolean/status representations."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    normalized = str(value).strip().lower()
    if normalized in ("true", "on", "online", "ok", "enabled", "running", "1"):
        return True
    if normalized in ("false", "off", "offline", "error", "disabled", "stopped", "0"):
        return False
    return default


def _decode_route_transport(transport: Any) -> dict[str, Any] | None:
    """Decode the current Relay gzip+base64 MapKit transport."""
    if not isinstance(transport, dict):
        return None
    snapshot_id = str(transport.get("snapshot_id") or "")
    if not snapshot_id:
        return None
    if not transport.get("available", True):
        return {
            "schema": "x50.route.v2",
            "snapshot_id": snapshot_id,
            "available": False,
            "observed_at_ms": integer(transport.get("published_at_ms"), 0),
        }
    if transport.get("codec") != "gzip+base64":
        return None
    encoded = transport.get("payload_b64")
    if not isinstance(encoded, str) or not encoded:
        return None
    try:
        route = json.loads(gzip.decompress(base64.b64decode(encoded)).decode("utf-8"))
    except (ValueError, TypeError, OSError, json.JSONDecodeError):
        return None
    if not isinstance(route, dict):
        return None
    return {
        "schema": "x50.route.v2",
        "snapshot_id": snapshot_id,
        "available": True,
        "observed_at_ms": integer(transport.get("published_at_ms"), 0),
        "route": route,
    }


@dataclass(slots=True)
class NormalizedMessage:
    """Compact state plus an optional heavy immutable route snapshot."""

    schema: str
    message_id: str
    installation_id: str
    device_id: str
    device_kind: str
    sample_time_ms: int
    received_time_ms: int
    compact: dict[str, Any]
    route_snapshot: dict[str, Any] | None


def normalize_message(
    raw: dict[str, Any],
    configured_installation_id: str,
    received_time_ms: int | None = None,
) -> NormalizedMessage:
    """Normalize the deployed v1 body or an x50.telemetry.v2 envelope."""
    if not isinstance(raw, dict):
        raise ValueError("payload must be a JSON object")
    received = received_time_ms or int(time.time() * 1000)
    schema = str(raw.get("schema") or "x50.telemetry.v1")
    if schema == "x50.telemetry.v2":
        payload = raw.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("v2 payload must be an object")
        installation_id = str(raw.get("installation_id") or configured_installation_id)
        message_id = str(raw.get("message_id") or f"v2-{received}")
        device_id = str(raw.get("device_id") or "relay")
        device_kind = str(raw.get("device_kind") or "head_unit")
        sample_time = integer(raw.get("sample_time_ms"), received) or received
    elif schema.startswith("x50.") and schema not in ("x50.telemetry.v1",):
        raise ValueError(f"unsupported schema: {schema}")
    else:
        payload = raw
        relay = payload.get("relay") if isinstance(payload.get("relay"), dict) else {}
        installation_id = configured_installation_id
        sample_time = (
            integer(relay.get("sample_timestamp_ms"))
            or integer(relay.get("timestamp_ms"))
            or received
        )
        message_id = str(
            relay.get("message_id")
            or relay.get("sample_id")
            or f"v1-{sample_time}"
        )
        device_id = str(relay.get("device_id") or "relay")
        device_kind = str(relay.get("device_kind") or "head_unit")

    compact = deepcopy(payload)
    navigation = compact.get("navigation")
    relay = compact.get("relay")
    route_transport_navigation = None
    route_transport_relay = None
    if isinstance(navigation, dict):
        route_transport_navigation = navigation.pop("route_transport", None)
    if isinstance(relay, dict):
        route_transport_relay = relay.pop("route_transport", None)
    route_transport = route_transport_navigation or route_transport_relay
    route_snapshot = _decode_route_transport(route_transport)

    compact["_x50"] = {
        "schema": schema,
        "message_id": message_id,
        "installation_id": installation_id,
        "device_id": device_id,
        "device_kind": device_kind,
        "sample_time_ms": sample_time,
        "received_time_ms": received,
    }
    return NormalizedMessage(
        schema=schema,
        message_id=message_id,
        installation_id=installation_id,
        device_id=device_id,
        device_kind=device_kind,
        sample_time_ms=sample_time,
        received_time_ms=received,
        compact=compact,
        route_snapshot=route_snapshot,
    )


def compact_summary(data: dict[str, Any]) -> dict[str, Any]:
    """Return the stable small state consumed by entities and Control Center."""
    location = _first(
        data,
        (
            "relay.gps_location",
            "vehicle_location",
        ),
        {},
    )
    if not isinstance(location, dict):
        location = {}
    latitude = _first(
        data,
        ("navigation.carlinkit_lat", "relay.gps_location.latitude", "relay.gps_location.lat"),
    )
    longitude = _first(
        data,
        ("navigation.carlinkit_lon", "relay.gps_location.longitude", "relay.gps_location.lon"),
    )
    return {
        "speed_kmh": finite(
            _first(data, ("vehicle_state.speed_kmh", "navigation.vehicle_speed_kmh"))
        ),
        "odometer_km": finite(
            _first(
                data,
                (
                    "vehicle_properties.ipk_total_odometer.kilometers",
                    "navigation.odometer_km",
                ),
            )
        ),
        "range_km": finite(
            _first(data, ("vehicle_properties.ipk_remaining_range.kilometers",))
        ),
        "ignition": _first(
            data, ("settings_global.ignition_state", "vehicle_state.ignition")
        ),
        "gear": _first(data, ("vehicle_state.gear", "vehicle_state.current_gear")),
        "latitude": finite(latitude),
        "longitude": finite(longitude),
        "gps_accuracy_m": finite(
            _first(
                data,
                ("navigation.carlinkit_accuracy_m", "relay.gps_location.accuracy"),
            )
        ),
        "gateway_version": _first(data, ("gateway.version",)),
        "gateway_online": boolean(
            _first(data, ("gateway.online", "gateway.status")),
            isinstance(data.get("gateway"), dict),
        ),
        "controls_enabled": boolean(
            _first(data, ("gateway.controls_enabled",)), False
        ),
        "relay_version": _first(data, ("relay.version",)),
        "relay_online": boolean(
            _first(data, ("relay.online",)),
            isinstance(data.get("relay"), dict),
        ),
        "fake_gps_enabled": boolean(
            _first(data, ("navigation.enabled", "gateway.fake_nav.enabled")), False
        ),
        "route_id": _first(
            data, ("navigation.exact_route_id", "navigation.route_id")
        ),
        "route_length_m": finite(_first(data, ("navigation.route_length_m",))),
        "route_progress_m": finite(_first(data, ("navigation.progress_m",))),
        "sample_time_ms": integer(nested(data, "_x50.sample_time_ms")),
        "received_time_ms": integer(nested(data, "_x50.received_time_ms")),
        "device_kind": str(nested(data, "_x50.device_kind", "head_unit")),
    }
