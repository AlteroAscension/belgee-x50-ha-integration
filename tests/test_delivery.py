"""Exercise actual intake and webhook code without a Home Assistant install."""
import ast
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "belgee_x50"
spec = importlib.util.spec_from_file_location("x50_delivery", ROOT / "delivery.py")
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class DeliveryTest(unittest.TestCase):
    def test_completion_and_reordering(self):
        active = {"complete": False, "observed_at_ms": 200}
        completed = {"complete": True, "observed_at_ms": 100}
        self.assertTrue(delivery.snapshot_is_newer(completed, active))
        self.assertFalse(delivery.snapshot_is_newer(active, completed))
        self.assertFalse(delivery.snapshot_is_newer(completed, completed))
        self.assertFalse(delivery.snapshot_is_newer({**active, "observed_at_ms": 100}, active))
        self.assertTrue(delivery.snapshot_is_newer({**completed, "observed_at_ms": 300}, completed))

    def test_deferred_does_not_update_either_live_source(self):
        tree = ast.parse((ROOT / "coordinator.py").read_text("utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "X50Coordinator")
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "async_ingest")
        namespace = {"NormalizedMessage": object, "is_deferred": delivery.is_deferred}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "coordinator.py", "exec"), namespace)
        receiver = types.SimpleNamespace(last_relay_message="current relay", last_gateway_message="current gateway")
        message = types.SimpleNamespace(compact={"relay": {"deferred_upload": True}})
        for transport in ("relay", "gateway"):
            self.assertFalse(namespace["async_ingest"](receiver, message, transport))
        self.assertEqual("current relay", receiver.last_relay_message)
        self.assertEqual("current gateway", receiver.last_gateway_message)

    def test_deferred_webhook_keeps_archive_and_suppresses_live_event(self):
        tree = ast.parse((ROOT / "__init__.py").read_text("utf-8"))
        setup = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_setup_entry")
        handler = next(n for n in setup.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "handle_webhook")
        events = []
        message = types.SimpleNamespace(installation_id="fixture", trip_journal_chunk={"chunk": 1},
            route_snapshot={"snapshot_id": "route"}, trajectory_snapshot={"snapshot_id": "trip"},
            device_id="car", device_kind="relay")
        async def executor(function, *args): return function(*args)
        hass = types.SimpleNamespace(config=types.SimpleNamespace(config_dir="unused"),
            async_add_executor_job=executor, bus=types.SimpleNamespace(async_fire=lambda name, body: events.append(name)))
        class Response:
            def __init__(self, **kwargs): self.status=kwargs["status"]
        coordinator = types.SimpleNamespace(async_ingest=lambda *args: False, store_trajectory=lambda *args: True)
        namespace = dict(Any=object, HomeAssistant=object, token="fixture-token", gateway_token="",
            installation_id="fixture", entry=types.SimpleNamespace(entry_id="fixture"), coordinator=coordinator,
            normalize_message=lambda *args: message, store_chunk=lambda *args: {"complete": True},
            web=types.SimpleNamespace(Response=Response), EVENT_TRIP_JOURNAL="journal",
            EVENT_TELEMETRY="live", EVENT_ROUTE_SNAPSHOT="route", EVENT_TRAJECTORY_SNAPSHOT="trajectory")
        exec(compile(ast.Module(body=[handler], type_ignores=[]), "webhook.py", "exec"), namespace)
        async def json_payload(): return {}
        request=types.SimpleNamespace(headers={"Authorization": "Bearer fixture-token"}, json=json_payload)
        response=asyncio.run(namespace["handle_webhook"](hass, "fixture", request))
        self.assertEqual(202, response.status)
        self.assertEqual(["journal", "route", "trajectory"], events)

    def test_auto_mode_keeps_live_relay_and_retains_gateway_for_failover(self):
        tree=ast.parse((ROOT / "coordinator.py").read_text("utf-8"))
        cls=next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name=="X50Coordinator")
        method=next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name=="async_ingest")
        namespace={"NormalizedMessage": object, "is_deferred": delivery.is_deferred}
        for mode in ("GATEWAY", "GATEWAY_POLL", "RELAY", "GATEWAY_PUSH", "AUTO"):
            namespace["CONNECTION_"+mode]=mode
        exec(compile(ast.Module(body=[method], type_ignores=[]), "coordinator.py", "exec"), namespace)
        applied=[]
        receiver=types.SimpleNamespace(connection_mode="AUTO", last_relay_message="current relay",
            _relay_is_fresh=lambda: True, _apply=lambda *args: applied.append(args))
        message=types.SimpleNamespace(compact={}, research_diagnostics=None)
        self.assertFalse(namespace["async_ingest"](receiver, message, "gateway"))
        self.assertIs(message, receiver.last_gateway_message)
        self.assertEqual([], applied)
        self.assertTrue(namespace["async_ingest"](receiver, message, "relay"))
        self.assertEqual([(message, "relay")], applied)
