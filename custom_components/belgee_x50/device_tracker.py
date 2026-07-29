"""Belgee X50 GPS tracker."""

from __future__ import annotations

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_INSTALLATION_ID, DATA_COORDINATOR, DOMAIN
from .entity import X50Entity


class X50Tracker(X50Entity, TrackerEntity):
    _attr_name = "Location"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator, installation_id: str) -> None:
        super().__init__(coordinator, installation_id, "location", "vehicle")

    @property
    def latitude(self) -> float | None:
        return self.coordinator.data.get("summary", {}).get("latitude")

    @property
    def longitude(self) -> float | None:
        return self.coordinator.data.get("summary", {}).get("longitude")

    @property
    def location_accuracy(self) -> int:
        return round(self.coordinator.data.get("summary", {}).get("gps_accuracy_m") or 0)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        [X50Tracker(coordinator, entry.data[CONF_INSTALLATION_ID])]
    )
