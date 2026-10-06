"""Ordering policy shared by live intake and retained trajectory snapshots."""

from __future__ import annotations


def is_deferred(compact: dict) -> bool:
    relay = compact.get("relay")
    return isinstance(relay, dict) and relay.get("deferred_upload") is True


def snapshot_is_newer(incoming: dict, current: dict | None) -> bool:
    """Completion wins; within the same state accept only a newer observation."""
    if current is None:
        return True
    complete, previous_complete = bool(incoming.get("complete")), bool(current.get("complete"))
    if complete != previous_complete:
        return complete
    return int(incoming.get("observed_at_ms") or 0) > int(current.get("observed_at_ms") or 0)
