"""Authenticated read-only trajectory retrieval for local HA add-ons."""

from __future__ import annotations

from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import DATA_COORDINATOR, DOMAIN
from .trip_journal import journal_directory, list_journals


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


class X50TripJournalListView(HomeAssistantView):
    """List complete diagnostic journals retained in HA's config directory."""

    url = "/api/belgee_x50/trip-journals"
    name = "api:belgee_x50:trip_journals"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        hass = request.app["hass"]
        result = []
        for entry_data in hass.data.get(DOMAIN, {}).values():
            if not isinstance(entry_data, dict):
                continue
            installation_id = entry_data.get("installation_id")
            if installation_id:
                result.extend(list_journals(hass.config.config_dir, installation_id))
        result.sort(key=lambda item: int(item.get("modified_ms") or 0))
        return web.json_response({"ok": True, "journals": result})


class X50TripJournalView(HomeAssistantView):
    """Download one completed compressed journal using a HA bearer token."""

    url = "/api/belgee_x50/trip-journals/{trip_id}"
    name = "api:belgee_x50:trip_journal"
    requires_auth = True

    async def get(self, request: web.Request, trip_id: str) -> web.Response:
        hass = request.app["hass"]
        if not trip_id or not trip_id.replace("-", "").isalnum() or len(trip_id) > 40:
            raise web.HTTPBadRequest(text="invalid_trip_id")
        for entry_data in hass.data.get(DOMAIN, {}).values():
            if not isinstance(entry_data, dict):
                continue
            installation_id = entry_data.get("installation_id")
            if not installation_id:
                continue
            path = journal_directory(hass.config.config_dir, installation_id) / f"{trip_id}.jsonl.gz"
            if path.is_file():
                return web.FileResponse(path, headers={
                    "Content-Type": "application/gzip",
                    "Content-Disposition": f'attachment; filename="{trip_id}.jsonl.gz"',
                })
        raise web.HTTPNotFound(text="trip_journal_not_found")
