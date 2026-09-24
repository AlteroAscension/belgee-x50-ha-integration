"""Durable receiver for chunked, opt-in Navigation trip journals."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import threading
from typing import Any

MAX_BYTES = 256 * 1024 * 1024
CHUNK_BYTES = 96 * 1024
_STORE_LOCK = threading.RLock()


def journal_directory(config_dir: str, installation_id: str) -> Path:
    safe_installation = re.sub(r"[^A-Za-z0-9_-]", "_", installation_id)[:100]
    return Path(config_dir) / "belgee_x50" / "trip_journals" / safe_installation


def store_chunk(config_dir: str, installation_id: str, chunk: dict[str, Any]) -> dict[str, Any]:
    """Append one verified-position chunk; exact retries are idempotent."""
    with _STORE_LOCK:
        return _store_chunk(config_dir, installation_id, chunk)


def _store_chunk(config_dir: str, installation_id: str, chunk: dict[str, Any]) -> dict[str, Any]:
    trip_id = str(chunk["id"])
    offset = int(chunk["offset"])
    total = int(chunk["total_bytes"])
    payload = bytes(chunk["chunk"])
    expected_hash = str(chunk["sha256"])
    if not re.fullmatch(r"\d{8}-\d{6}-[0-9a-f]{8}", trip_id):
        raise ValueError("invalid_trip_id")
    if (total <= 0 or total > MAX_BYTES or offset < 0
            or offset % CHUNK_BYTES or not payload or len(payload) > CHUNK_BYTES
            or offset + len(payload) > total
            or bool(chunk.get("complete")) != (offset + len(payload) == total)):
        raise ValueError("invalid_trip_chunk_bounds")
    directory = journal_directory(config_dir, installation_id)
    directory.mkdir(parents=True, exist_ok=True)
    final_path = directory / f"{trip_id}.jsonl.gz"
    partial_path = directory / f"{trip_id}.jsonl.gz.part"
    if final_path.exists():
        if final_path.stat().st_size == total and _sha256(final_path) == expected_hash:
            return {"id": trip_id, "complete": True, "duplicate": True,
                    "received_bytes": total, "total_bytes": total}
        raise ValueError("journal_already_finalized_with_different_content")

    current_size = partial_path.stat().st_size if partial_path.exists() else 0
    if offset < current_size:
        with partial_path.open("rb") as stream:
            stream.seek(offset)
            if stream.read(len(payload)) != payload:
                raise ValueError("conflicting_duplicate_chunk")
        return {"id": trip_id, "complete": False, "duplicate": True,
                "received_bytes": current_size, "total_bytes": total}
    if offset != current_size:
        raise ValueError("trip_journal_chunk_out_of_order")
    mode = "ab" if partial_path.exists() else "wb"
    with partial_path.open(mode) as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    current_size += len(payload)
    complete = current_size == total
    if complete:
        if _sha256(partial_path) != expected_hash:
            partial_path.unlink(missing_ok=True)
            raise ValueError("trip_journal_sha256_mismatch")
        partial_path.replace(final_path)
    return {"id": trip_id, "complete": complete, "duplicate": False,
            "received_bytes": current_size, "total_bytes": total}


def list_journals(config_dir: str, installation_id: str) -> list[dict[str, Any]]:
    directory = journal_directory(config_dir, installation_id)
    if not directory.is_dir():
        return []
    result = []
    for path in sorted(directory.glob("*.jsonl.gz"), key=lambda item: item.stat().st_mtime):
        result.append({"id": path.name[:-9], "size_bytes": path.stat().st_size,
                       "sha256": _sha256(path), "complete": True,
                       "modified_ms": int(path.stat().st_mtime * 1000)})
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(128 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
