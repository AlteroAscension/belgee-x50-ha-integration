"""Protocol tests runnable without Home Assistant."""

from __future__ import annotations

import base64
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "belgee_x50_models",
    ROOT / "custom_components" / "belgee_x50" / "models.py",
)
models = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = models
SPEC.loader.exec_module(models)


class NormalizeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(
            (ROOT / "tests" / "fixtures" / "telemetry_v1.json").read_text("utf-8")
        )

    def test_current_relay_payload_is_normalized(self) -> None:
        message = models.normalize_message(
            self.fixture, "car-main", received_time_ms=1780000000100
        )
        summary = models.compact_summary(message.compact)
        self.assertEqual("x50.telemetry.v1", message.schema)
        self.assertEqual("head_unit", message.device_kind)
        self.assertEqual(54.2, summary["speed_kmh"])
        self.assertEqual(26175.4, summary["odometer_km"])
        self.assertEqual(55.7, summary["latitude"])
        self.assertTrue(summary["fake_gps_enabled"])

    def test_v2_envelope_keeps_identity(self) -> None:
        message = models.normalize_message(
            {
                "schema": "x50.telemetry.v2",
                "message_id": "m-1",
                "installation_id": "car-main",
                "device_id": "relay-1",
                "device_kind": "head_unit",
                "sample_time_ms": 1780000000000,
                "payload": self.fixture,
            },
            "car-main",
            received_time_ms=1780000000100,
        )
        self.assertEqual("m-1", message.message_id)
        self.assertEqual("relay-1", message.device_id)

    def test_gateway_push_does_not_report_absent_relay_online(self) -> None:
        message = models.normalize_message(
            {
                "schema": "x50.telemetry.v2",
                "message_id": "gateway-1",
                "installation_id": "car-main",
                "device_id": "gateway-1",
                "device_kind": "gateway",
                "sample_time_ms": 1780000000000,
                "payload": {
                    "gateway": {"version": "2.25.0-ha-direct-push"},
                    "vehicle_state": {"speed_kmh": 42.0},
                },
            },
            "car-main",
            received_time_ms=1780000000100,
        )
        summary = models.compact_summary(message.compact)
        self.assertTrue(summary["gateway_online"])
        self.assertFalse(summary["relay_online"])
        self.assertEqual(42.0, summary["speed_kmh"])

    def test_route_is_removed_from_entity_payload(self) -> None:
        route = {"exact_route_id": "route-1", "exact_points": [[55.7, 37.5], [55.8, 37.6]]}
        transport = {
            "snapshot_id": "route-1:1",
            "available": True,
            "codec": "gzip+base64",
            "payload_b64": base64.b64encode(
                gzip.compress(json.dumps(route).encode())
            ).decode(),
        }
        self.fixture["navigation"]["route_transport"] = transport
        self.fixture["relay"]["route_transport"] = transport
        message = models.normalize_message(self.fixture, "car-main")
        self.assertNotIn("route_transport", message.compact["navigation"])
        self.assertNotIn("route_transport", message.compact["relay"])
        self.assertEqual("route-1:1", message.route_snapshot["snapshot_id"])
        self.assertEqual(route, message.route_snapshot["route"])

    def test_unknown_major_schema_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            models.normalize_message(
                {"schema": "x50.telemetry.v3", "payload": {}}, "car-main"
            )


if __name__ == "__main__":
    unittest.main()
