"""Push coordinator for Belgee X50 telemetry."""

from __future__ import annotations

from datetime import timedelta
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .models import NormalizedMessage, compact_summary


class X50Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Keep the latest compact Relay state and age it without network polling."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, stale_after: int
    ) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=min(30, max(10, stale_after // 3))),
        )
        self.stale_after = stale_after
        self.last_message: NormalizedMessage | None = None
        self.async_set_updated_data({"summary": {}, "raw": {}})

    async def _async_update_data(self) -> dict[str, Any]:
        # The timer deliberately republishes the same push state so entity
        # availability changes after stale_after even when Relay is silent.
        return self.data

    def async_ingest(self, message: NormalizedMessage) -> None:
        self.last_message = message
        self.async_set_updated_data(
            {"summary": compact_summary(message.compact), "raw": message.compact}
        )

    @property
    def telemetry_available(self) -> bool:
        if self.last_message is None:
            return False
        age = time.time() - self.last_message.received_time_ms / 1000
        return age <= self.stale_after
