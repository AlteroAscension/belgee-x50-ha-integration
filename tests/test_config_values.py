"""Small pure checks for config-flow optional value handling."""

from __future__ import annotations

import unittest


def optional_text(value: object | None) -> str:
    """Mirror optional URL field normalization in the config flow."""
    return str(value or "").strip()


class ConfigValueTests(unittest.TestCase):
    def test_blank_optional_gateway_url_is_not_literal_none(self) -> None:
        self.assertEqual("", optional_text(None))
        self.assertEqual("", optional_text(""))
        self.assertEqual("", optional_text("  "))
        self.assertEqual("http://gateway:8080", optional_text(" http://gateway:8080 "))


if __name__ == "__main__":
    unittest.main()
