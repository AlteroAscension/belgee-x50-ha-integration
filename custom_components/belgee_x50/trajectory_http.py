"""Authenticated read-only trajectory retrieval for local HA add-ons."""

from __future__ import annotations

from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import DATA_COORDINATOR, DOMAIN


class X50TrajectoryLatestView(HomeAssistantView):
    """Return the latest retained steering snapshot for an installation."""

    url = "/api/belgee_x50/trajectory/latest"
    name = "api:belgee_x50:trajectory:latest"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        installations = request.app["hass"].data.get(DOMAIN, {})
        snapshot = None
        for entry_data in installations.values():
            coordinator = entry_data.get(DATA_COORDINATOR) if isinstance(entry_data, dict) else None
            if coordinator is not None:
                snapshot = coordinator.trajectory_snapshot()
            if snapshot is not None:
                break
        if snapshot is None:
            raise web.HTTPNotFound(text="trajectory_not_found")
        return web.json_response(snapshot)
