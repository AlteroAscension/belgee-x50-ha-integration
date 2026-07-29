"""Belgee X50 sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_INSTALLATION_ID, DATA_COORDINATOR, DOMAIN
from .entity import X50Entity


@dataclass(frozen=True, kw_only=True)
class X50SensorDescription(SensorEntityDescription):
    device_kind: str = "vehicle"
    diagnostic: bool = False


DESCRIPTIONS = (
    X50SensorDescription(
        key="speed_kmh", name="Speed", native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED, state_class=SensorStateClass.MEASUREMENT
    ),
    X50SensorDescription(
        key="odometer_km", name="Odometer", native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL_INCREASING
    ),
    X50SensorDescription(
        key="range_km", name="Range", native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT
    ),
    X50SensorDescription(key="gear", name="Gear"),
    X50SensorDescription(
        key="gateway_version", name="Version", device_kind="gateway", diagnostic=True
    ),
    X50SensorDescription(
        key="relay_version", name="Version", device_kind="relay", diagnostic=True
    ),
    X50SensorDescription(
        key="route_length_m", name="Route length", device_kind="navigation",
        native_unit_of_measurement=UnitOfLength.METERS, device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT
    ),
    X50SensorDescription(
        key="route_progress_m", name="Route progress", device_kind="navigation",
        native_unit_of_measurement=UnitOfLength.METERS, device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT
    ),
    X50SensorDescription(
        key="gps_accuracy_m", name="GPS accuracy", device_kind="relay",
        native_unit_of_measurement=UnitOfLength.METERS, device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT, diagnostic=True
    ),
    X50SensorDescription(
        key="connection_mode", name="Connection mode", device_kind="gateway",
        diagnostic=True
    ),
    X50SensorDescription(
        key="active_transport", name="Active transport", device_kind="gateway",
        diagnostic=True
    ),
)


class X50Sensor(X50Entity, SensorEntity):
    def __init__(self, coordinator: Any, installation_id: str, description: X50SensorDescription) -> None:
        super().__init__(coordinator, installation_id, description.key, description.device_kind)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        if description.diagnostic:
            from homeassistant.helpers.entity import EntityCategory
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.get("summary", {}).get(self.entity_description.key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    installation_id = entry.data[CONF_INSTALLATION_ID]
    async_add_entities(
        X50Sensor(coordinator, installation_id, description)
        for description in DESCRIPTIONS
    )
