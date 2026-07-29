"""Public endpoint URL tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "belgee_x50_urls",
    ROOT / "custom_components" / "belgee_x50" / "urls.py",
)
urls = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = urls
SPEC.loader.exec_module(urls)


class PublicBaseUrlTests(unittest.TestCase):
    def test_normalizes_trailing_slash(self) -> None:
        self.assertEqual(
            urls.normalize_public_base_url(" https://ha.example.com/ "),
            "https://ha.example.com",
        )

    def test_keeps_reverse_proxy_path(self) -> None:
        self.assertEqual(
            urls.normalize_public_base_url("https://example.com/home-assistant/"),
            "https://example.com/home-assistant",
        )

    def test_rejects_incomplete_address(self) -> None:
        with self.assertRaises(ValueError):
            urls.normalize_public_base_url("ha.example.com")

    def test_rejects_query_or_fragment(self) -> None:
        with self.assertRaises(ValueError):
            urls.normalize_public_base_url("https://ha.example.com/?token=secret")


if __name__ == "__main__":
    unittest.main()
