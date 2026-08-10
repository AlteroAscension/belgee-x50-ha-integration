"""One-time runtime initialization shared by setup and Config Flow."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DATA_PAIRING_MANAGER, DOMAIN
from .pairing import PairingManager
from .pairing_http import X50PairingClaimView, X50PairingStatusView


def ensure_pairing_runtime(hass: HomeAssistant) -> PairingManager:
    """Return the pairing manager and register its HTTP views exactly once.

    Config Flow can be executed before ``async_setup`` for a custom
    integration.  Keeping this initialization here prevents the first setup
    screen from failing while it creates a short-lived pairing code.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    manager = domain_data.get(DATA_PAIRING_MANAGER)
    if isinstance(manager, PairingManager):
        return manager
    manager = PairingManager()
    domain_data[DATA_PAIRING_MANAGER] = manager
    hass.http.register_view(X50PairingClaimView)
    hass.http.register_view(X50PairingStatusView)
    return manager
