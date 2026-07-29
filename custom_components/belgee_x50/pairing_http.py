"""Unauthenticated, short-lived Relay pairing HTTP endpoints."""

from __future__ import annotations

from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import (
    DATA_PAIRING_MANAGER,
    DOMAIN,
    PAIRING_CLAIM_PATH,
    PAIRING_STATUS_PATH,
)
from .pairing import PairingError, PairingManager


def _manager(request: web.Request) -> PairingManager:
    return request.app["hass"].data[DOMAIN][DATA_PAIRING_MANAGER]


async def _json(request: web.Request) -> dict:
    try:
        value = await request.json()
    except (ValueError, TypeError) as error:
        raise web.HTTPBadRequest(text="invalid json") from error
    if not isinstance(value, dict):
        raise web.HTTPBadRequest(text="invalid json")
    return value


class X50PairingClaimView(HomeAssistantView):
    """Claim a displayed one-time code without receiving credentials yet."""

    url = PAIRING_CLAIM_PATH
    name = "api:belgee_x50:pairing:claim"
    requires_auth = False

    async def post(self, request: web.Request) -> web.Response:
        payload = await _json(request)
        try:
            result = _manager(request).claim(
                payload.get("code", ""),
                device_id=str(payload.get("device_id", "")),
                device_name=str(payload.get("device_name", "X50 Relay")),
                relay_version=str(payload.get("relay_version", "unknown")),
                request_nonce=str(payload.get("request_nonce", "")),
            )
        except PairingError as error:
            status = 409 if error.reason == "already_claimed" else 400
            return web.json_response(
                {"ok": False, "error": error.reason}, status=status
            )
        return web.json_response(result, status=202)


class X50PairingStatusView(HomeAssistantView):
    """Poll for user confirmation and then return the credentials once."""

    url = PAIRING_STATUS_PATH
    name = "api:belgee_x50:pairing:status"
    requires_auth = False

    async def post(self, request: web.Request) -> web.Response:
        payload = await _json(request)
        try:
            result = _manager(request).status(
                str(payload.get("claim_id", "")),
                str(payload.get("claim_secret", "")),
            )
        except PairingError as error:
            return web.json_response(
                {"ok": False, "error": error.reason}, status=400
            )
        status = 200 if result["status"] == "paired" else 202
        return web.json_response(result, status=status)
