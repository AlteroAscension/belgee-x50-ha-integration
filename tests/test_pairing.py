"""Pairing state-machine tests independent of Home Assistant imports."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "belgee_x50_pairing",
    ROOT / "custom_components" / "belgee_x50" / "pairing.py",
)
pairing = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = pairing
SPEC.loader.exec_module(pairing)
PairingError = pairing.PairingError
PairingManager = pairing.PairingManager


class PairingManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1000.0
        self.manager = PairingManager(clock=lambda: self.now, ttl_seconds=300)
        self.credentials = {
            "telemetry_url": "https://ha.example/api/webhook/private",
            "bearer_token": "private-token-value",
            "installation_id": "car",
        }

    def test_credentials_are_withheld_until_user_confirmation(self) -> None:
        session = self.manager.open(self.credentials)
        claim = self.manager.claim(
            session.code,
            device_id="relay-123",
            device_name="Relay",
            relay_version="2.16.0",
            request_nonce="unique-request-nonce-123",
        )
        pending = self.manager.status(
            claim["claim_id"], claim["claim_secret"]
        )
        self.assertEqual("pending_confirmation", pending["status"])
        self.assertNotIn("bearer_token", pending)

        self.manager.confirm(session.session_id)
        paired = self.manager.status(
            claim["claim_id"], claim["claim_secret"]
        )
        self.assertEqual("paired", paired["status"])
        self.assertEqual(self.credentials["bearer_token"], paired["bearer_token"])

    def test_claim_retry_requires_same_device_and_nonce(self) -> None:
        session = self.manager.open(self.credentials)
        first = self.manager.claim(
            session.code,
            device_id="relay-123",
            device_name="Relay",
            relay_version="2.16.0",
            request_nonce="unique-request-nonce-123",
        )
        retry = self.manager.claim(
            session.code,
            device_id="relay-123",
            device_name="Relay",
            relay_version="2.16.0",
            request_nonce="unique-request-nonce-123",
        )
        self.assertEqual(first["claim_secret"], retry["claim_secret"])
        with self.assertRaisesRegex(PairingError, "already_claimed"):
            self.manager.claim(
                session.code,
                device_id="relay-123",
                device_name="Relay",
                relay_version="2.16.0",
                request_nonce="different-request-nonce",
            )

    def test_expired_code_and_claim_are_removed(self) -> None:
        session = self.manager.open(self.credentials)
        claim = self.manager.claim(
            session.code,
            device_id="relay-123",
            device_name="Relay",
            relay_version="2.16.0",
            request_nonce="unique-request-nonce-123",
        )
        self.now += 301
        with self.assertRaisesRegex(PairingError, "invalid_or_expired_code"):
            self.manager.claim(
                session.code,
                device_id="relay-123",
                device_name="Relay",
                relay_version="2.16.0",
                request_nonce="unique-request-nonce-123",
            )
        with self.assertRaisesRegex(PairingError, "invalid_claim"):
            self.manager.status(claim["claim_id"], claim["claim_secret"])

    def test_code_format_is_human_friendly(self) -> None:
        session = self.manager.open(self.credentials)
        self.assertEqual(8, len(session.code))
        self.assertNotIn("0", session.code)
        self.assertNotIn("O", session.code)
        self.assertEqual(
            session.code, self.manager.normalize_code(
                f"{session.code[:4]}-{session.code[4:].lower()}"
            )
        )


if __name__ == "__main__":
    unittest.main()
