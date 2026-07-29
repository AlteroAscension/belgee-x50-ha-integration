"""Direct Gateway URL and payload tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "belgee_x50_gateway",
    ROOT / "custom_components" / "belgee_x50" / "gateway.py",
)
gateway = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = gateway
SPEC.loader.exec_module(gateway)


class GatewayTransportTests(unittest.TestCase):
    def test_normalizes_base_and_telemetry_url(self) -> None:
        self.assertEqual(
            "http://gateway.example:8080",
            gateway.normalize_gateway_url(
                "http://gateway.example:8080/api/telemetry"
            ),
        )
        self.assertEqual(
            "https://proxy.example/x50/api/telemetry",
            gateway.gateway_telemetry_url("https://proxy.example/x50/"),
        )
        self.assertEqual(
            "https://proxy.example/x50/api/fake_nav/route",
            gateway.gateway_route_url("https://proxy.example/x50/"),
        )

    def test_rejects_incomplete_or_parameterized_url(self) -> None:
        for value in ("gateway:8080", "ftp://gateway", "http://gateway/?token=x"):
            with self.assertRaises(ValueError):
                gateway.normalize_gateway_url(value)

    def test_token_header_is_optional(self) -> None:
        self.assertEqual({}, gateway.gateway_headers(""))
        self.assertEqual(
            {"X-X50-Token": "secret"}, gateway.gateway_headers(" secret ")
        )

    def test_payload_must_be_an_object(self) -> None:
        with self.assertRaises(ValueError):
            gateway.validate_gateway_payload([])

    def test_route_revision_uses_mapkit_identity(self) -> None:
        self.assertEqual(
            "route-a:2:7",
            gateway.gateway_route_revision(
                {
                    "navigation": {
                        "route_available": True,
                        "route_source": "mapkit",
                        "exact_route_id": "route-a",
                        "route_activation_count": 2,
                        "route_generation": 7,
                    }
                }
            ),
        )
        self.assertEqual(
            "none",
            gateway.gateway_route_revision(
                {
                    "navigation": {
                        "route_available": True,
                        "route_source": "guidance_history",
                    }
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()
