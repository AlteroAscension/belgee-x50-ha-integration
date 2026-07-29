"""Constants for the Belgee X50 integration."""

from __future__ import annotations

DOMAIN = "belgee_x50"
PLATFORMS = ("sensor", "binary_sensor", "device_tracker")

CONF_INSTALLATION_ID = "installation_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_WEBHOOK_ID = "webhook_id"
CONF_NAME = "name"
CONF_STALE_AFTER = "stale_after_seconds"
CONF_PUBLIC_BASE_URL = "public_base_url"
CONF_START_PAIRING = "start_pairing"

DEFAULT_NAME = "Belgee X50"
DEFAULT_STALE_AFTER = 120
MIN_STALE_AFTER = 30
MAX_STALE_AFTER = 900

EVENT_TELEMETRY = "belgee_x50_telemetry"
EVENT_ROUTE_SNAPSHOT = "belgee_x50_route_snapshot"

DATA_COORDINATOR = "coordinator"
DATA_WEBHOOK_URL = "webhook_url"
DATA_PAIRING_MANAGER = "pairing_manager"

PAIRING_CLAIM_PATH = "/api/belgee_x50/pairing/claim"
PAIRING_STATUS_PATH = "/api/belgee_x50/pairing/status"
PAIRING_TTL_SECONDS = 300

ATTRIBUTION = "Data supplied by X50 Relay"
