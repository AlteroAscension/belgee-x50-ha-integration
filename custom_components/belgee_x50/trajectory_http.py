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


class X50TrajectoryListView(HomeAssistantView):
    """List bounded trajectory metadata for the persistent simulator journal."""

    url = "/api/belgee_x50/trajectories"
    name = "api:belgee_x50:trajectories"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        installations = request.app["hass"].data.get(DOMAIN, {})
        trajectories = []
        for entry_data in installations.values():
            coordinator = entry_data.get(DATA_COORDINATOR) if isinstance(entry_data, dict) else None
            if coordinator is not None:
                trajectories.extend(coordinator.trajectory_snapshots_list())
        trajectories.sort(key=lambda item: int(item.get("observed_at_ms") or 0))
        return web.json_response({"ok": True, "trajectories": trajectories})


class X50TrajectoryView(HomeAssistantView):
    """Return one authenticated retained trajectory by stable snapshot ID."""

    url = "/api/belgee_x50/trajectories/{snapshot_id}"
    name = "api:belgee_x50:trajectory"
    requires_auth = True

    async def get(self, request: web.Request, snapshot_id: str) -> web.Response:
        installations = request.app["hass"].data.get(DOMAIN, {})
        for entry_data in installations.values():
            coordinator = entry_data.get(DATA_COORDINATOR) if isinstance(entry_data, dict) else None
            if coordinator is not None:
                snapshot = coordinator.trajectory_snapshot(snapshot_id)
                if snapshot is not None:
                    return web.json_response(snapshot)
        raise web.HTTPNotFound(text="trajectory_not_found")
