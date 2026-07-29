"""Guard imports that Home Assistant resolves before Config Flow can open."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "belgee_x50"


class HomeAssistantImportBoundaryTest(unittest.TestCase):
    def test_webhook_comes_from_components_package(self) -> None:
        tree = ast.parse((COMPONENT / "__init__.py").read_text("utf-8"))
        imports = {
            (node.module, alias.name)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertIn(("homeassistant.components", "webhook"), imports)
        self.assertNotIn(("homeassistant.helpers", "webhook"), imports)

    def test_config_flow_module_exists_for_manifest(self) -> None:
        self.assertTrue((COMPONENT / "config_flow.py").is_file())


if __name__ == "__main__":
    unittest.main()
