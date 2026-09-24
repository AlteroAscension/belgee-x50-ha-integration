"""Idempotent bounded storage tests for full-trip diagnostic archives."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "belgee_x50_trip_journal",
    ROOT / "custom_components" / "belgee_x50" / "trip_journal.py",
)
store = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = store
SPEC.loader.exec_module(store)


class TripJournalStoreTest(unittest.TestCase):
    def test_chunks_are_durable_ordered_and_retry_safe(self) -> None:
        first = b"a" * (96 * 1024)
        last = b"tail"
        content = first + last
        trip_id = "20260924-150707-a1b2c3d4"
        with tempfile.TemporaryDirectory() as config_dir:
            result = store.store_chunk(config_dir, "car-main", {
                "id": trip_id, "offset": 0, "total_bytes": len(content),
                "chunk": first, "sha256": "", "complete": False,
            })
            self.assertFalse(result["complete"])
            duplicate = store.store_chunk(config_dir, "car-main", {
                "id": trip_id, "offset": 0, "total_bytes": len(content),
                "chunk": first, "sha256": "", "complete": False,
            })
            self.assertTrue(duplicate["duplicate"])
            with self.assertRaises(ValueError):
                store.store_chunk(config_dir, "car-main", {
                    "id": trip_id, "offset": len(first) + 1,
                    "total_bytes": len(content), "chunk": last,
                    "sha256": "", "complete": True,
                })
            final = store.store_chunk(config_dir, "car-main", {
                "id": trip_id, "offset": len(first), "total_bytes": len(content),
                "chunk": last, "sha256": hashlib.sha256(content).hexdigest(),
                "complete": True,
            })
            self.assertTrue(final["complete"])
            retry = store.store_chunk(config_dir, "car-main", {
                "id": trip_id, "offset": len(first), "total_bytes": len(content),
                "chunk": last, "sha256": hashlib.sha256(content).hexdigest(),
                "complete": True,
            })
            self.assertTrue(retry["duplicate"])
            self.assertEqual(trip_id, store.list_journals(config_dir, "car-main")[0]["id"])


if __name__ == "__main__":
    unittest.main()
