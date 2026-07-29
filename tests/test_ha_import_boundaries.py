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

    def test_config_flow_schema_has_no_custom_callable_validator(self) -> None:
        tree = ast.parse((COMPONENT / "config_flow.py").read_text("utf-8"))
        custom_validator_names = {
            node.id
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "vol"
            and call.func.attr == "All"
            for node in call.args
            if isinstance(node, ast.Name) and node.id.startswith("_")
        }
        self.assertEqual(set(), custom_validator_names)


if __name__ == "__main__":
    unittest.main()
