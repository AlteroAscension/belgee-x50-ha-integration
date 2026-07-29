"""Belgee X50 binary sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_INSTALLATION_ID, DATA_COORDINATOR, DOMAIN
from .entity import X50Entity


@dataclass(frozen=True, kw_only=True)
class X50BinaryDescription(BinarySensorEntityDescription):
    device_kind: str
    diagnostic: bool = False


DESCRIPTIONS = (
    X50BinaryDescription(
        key="ignition", name="Ignition", device_kind="vehicle",
        device_class=BinarySensorDeviceClass.POWER
    ),
    X50BinaryDescription(
        key="gateway_online", name="Connectivity", device_kind="gateway",
        device_class=BinarySensorDeviceClass.CONNECTIVITY, diagnostic=True
    ),
    X50BinaryDescription(
        key="controls_enabled", name="Remote control", device_kind="gateway",
        device_class=BinarySensorDeviceClass.RUNNING, diagnostic=True
    ),
    X50BinaryDescription(
        key="relay_online", name="Connectivity", device_kind="relay",
        device_class=BinarySensorDeviceClass.CONNECTIVITY, diagnostic=True
    ),
    X50BinaryDescription(
        key="fake_gps_enabled", name="FakeGPS", device_kind="navigation",
        device_class=BinarySensorDeviceClass.RUNNING
    ),
)


class X50BinarySensor(X50Entity, BinarySensorEntity):
    def __init__(self, coordinator: Any, installation_id: str, description: X50BinaryDescription) -> None:
        super().__init__(coordinator, installation_id, description.key, description.device_kind)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_device_class = description.device_class
        if description.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get("summary", {}).get(self.entity_description.key)
        if value is None:
            return None
        if self.entity_description.key == "ignition":
            return str(value).lower() not in ("0", "off", "false", "unknown")
        return bool(value)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    installation_id = entry.data[CONF_INSTALLATION_ID]
    async_add_entities(
        X50BinarySensor(coordinator, installation_id, description)
        for description in DESCRIPTIONS
    )
