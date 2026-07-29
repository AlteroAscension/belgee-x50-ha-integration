"""Direct Gateway transport helpers."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit


def normalize_gateway_url(value: str) -> str:
    """Validate and normalize a directly reachable Gateway base URL."""
    raw = str(value or "").strip()
    parsed = urlsplit(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Enter a complete Gateway URL")
    if parsed.query or parsed.fragment:
        raise ValueError("Gateway URL cannot contain query or fragment")
    path = parsed.path.rstrip("/")
    if path.endswith("/api/telemetry"):
        path = path[: -len("/api/telemetry")]
    return urlunsplit((parsed.scheme, parsed.netloc, path.rstrip("/"), "", ""))


def gateway_telemetry_url(base_url: str) -> str:
    return f"{normalize_gateway_url(base_url)}/api/telemetry"


def gateway_route_url(base_url: str) -> str:
    return f"{normalize_gateway_url(base_url)}/api/fake_nav/route"


def gateway_headers(token: str | None) -> dict[str, str]:
    """Attach the token for forward compatibility with protected reads."""
    value = str(token or "").strip()
    return {"X-X50-Token": value} if value else {}


def validate_gateway_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Gateway telemetry must be a JSON object")
    return value


def gateway_route_revision(telemetry: dict[str, Any]) -> str:
    """Return the compact MapKit identity used to deduplicate heavy reads."""
    navigation = telemetry.get("navigation")
    if not isinstance(navigation, dict):
        return "none"
    if not navigation.get("route_available"):
        return "none"
    if navigation.get("route_source") != "mapkit":
        return "none"
    identity = str(
        navigation.get("route_identity")
        or navigation.get("exact_route_id")
        or "mapkit"
    )
    return (
        f"{identity}:"
        f"{int(navigation.get('route_activation_count') or 0)}:"
        f"{int(navigation.get('route_generation') or 0)}"
    )
