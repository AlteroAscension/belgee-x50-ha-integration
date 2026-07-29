"""Shared Belgee X50 entity base."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import X50Coordinator


class X50Entity(CoordinatorEntity[X50Coordinator]):
    """Base entity backed by the push coordinator."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: X50Coordinator,
        installation_id: str,
        key: str,
        device_kind: str = "vehicle",
    ) -> None:
        super().__init__(coordinator)
        self._installation_id = installation_id
        self._device_kind = device_kind
        self._attr_unique_id = f"{installation_id}_{device_kind}_{key}"

    @property
    def available(self) -> bool:
        return self.coordinator.telemetry_available

    @property
    def device_info(self) -> DeviceInfo:
        names = {
            "vehicle": ("Belgee X50", "Belgee", "X50"),
            "gateway": ("X50 Gateway", "LesNIK", "X50 Gateway"),
            "navigation": ("X50 Navigation", "LesNIK", "X50 Navigation"),
            "relay": ("X50 Relay", "LesNIK", "X50 Relay"),
        }
        name, manufacturer, model = names[self._device_kind]
        summary: dict[str, Any] = self.coordinator.data.get("summary", {})
        version = summary.get(f"{self._device_kind}_version")
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._installation_id}_{self._device_kind}")},
            name=name,
            manufacturer=manufacturer,
            model=model,
            sw_version=str(version) if version else None,
        )
