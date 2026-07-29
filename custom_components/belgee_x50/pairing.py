"""Short-lived, user-confirmed Relay pairing sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import secrets
import time
from typing import Any, Callable

PAIRING_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
PAIRING_CODE_LENGTH = 8


class PairingError(ValueError):
    """Pairing request cannot be completed."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class PairingSession:
    """One pending HA-to-Relay credential exchange."""

    session_id: str
    code: str
    expires_at: float
    credentials: dict[str, str]
    claimed_device_id: str | None = None
    claimed_device_name: str | None = None
    claimed_relay_version: str | None = None
    claimed_nonce: str | None = None
    claimed_source_kind: str | None = None
    claim_id: str | None = None
    claim_secret: str | None = None
    fingerprint: str | None = None
    confirmed: bool = False
    failed_attempts: int = 0
    created_at: float = field(default_factory=time.time)

    @property
    def claimed(self) -> bool:
        return self.claim_id is not None


class PairingManager:
    """Own bounded, expiring pairing state kept only in HA memory."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.time,
        ttl_seconds: int = 300,
    ) -> None:
        self._clock = clock
        self._ttl_seconds = ttl_seconds
        self._sessions: dict[str, PairingSession] = {}
        self._codes: dict[str, str] = {}
        self._claims: dict[str, str] = {}

    def open(self, credentials: dict[str, str]) -> PairingSession:
        self.cleanup()
        code = self._new_code()
        session = PairingSession(
            session_id=secrets.token_urlsafe(18),
            code=code,
            expires_at=self._clock() + self._ttl_seconds,
            credentials=dict(credentials),
        )
        self._sessions[session.session_id] = session
        self._codes[code] = session.session_id
        return session

    def get(self, session_id: str) -> PairingSession | None:
        self.cleanup()
        return self._sessions.get(session_id)

    def cancel(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is None:
            return
        self._codes.pop(session.code, None)
        if session.claim_id:
            self._claims.pop(session.claim_id, None)

    def claim(
        self,
        code: str,
        *,
        device_id: str,
        device_name: str,
        relay_version: str,
        request_nonce: str,
        source_kind: str = "relay",
    ) -> dict[str, Any]:
        self.cleanup()
        normalized = self.normalize_code(code)
        session_id = self._codes.get(normalized)
        session = self._sessions.get(session_id or "")
        if session is None:
            raise PairingError("invalid_or_expired_code")
        if not device_id or len(device_id) > 128:
            raise PairingError("invalid_device")
        if len(request_nonce) < 16 or len(request_nonce) > 128:
            raise PairingError("invalid_nonce")
        expected_source = str(session.credentials.get("source_kind", "relay"))
        if source_kind not in ("relay", "gateway") \
                or source_kind != expected_source:
            raise PairingError("wrong_device_type")

        if session.claimed:
            if (
                session.claimed_device_id != device_id
                or not secrets.compare_digest(
                    session.claimed_nonce or "", request_nonce
                )
                or session.claimed_source_kind != source_kind
            ):
                raise PairingError("already_claimed")
        else:
            session.claimed_device_id = device_id
            session.claimed_device_name = (device_name or "X50 Relay")[:80]
            session.claimed_relay_version = (relay_version or "unknown")[:40]
            session.claimed_nonce = request_nonce
            session.claimed_source_kind = source_kind
            session.claim_id = secrets.token_urlsafe(18)
            session.claim_secret = secrets.token_urlsafe(32)
            digest = hashlib.sha256(
                f"{session.session_id}:{device_id}:{session.claim_secret}".encode()
            ).hexdigest().upper()
            session.fingerprint = f"{digest[:4]}-{digest[4:8]}"
            self._claims[session.claim_id] = session.session_id

        return {
            "ok": True,
            "status": "pending_confirmation",
            "claim_id": session.claim_id,
            "claim_secret": session.claim_secret,
            "fingerprint": session.fingerprint,
            "expires_in": max(0, int(session.expires_at - self._clock())),
        }

    def confirm(self, session_id: str) -> PairingSession:
        session = self.get(session_id)
        if session is None:
            raise PairingError("expired")
        if not session.claimed:
            raise PairingError("not_claimed")
        session.confirmed = True
        return session

    def status(self, claim_id: str, claim_secret: str) -> dict[str, Any]:
        self.cleanup()
        session_id = self._claims.get(claim_id)
        session = self._sessions.get(session_id or "")
        if (
            session is None
            or not secrets.compare_digest(session.claim_secret or "", claim_secret or "")
        ):
            raise PairingError("invalid_claim")
        if not session.confirmed:
            return {
                "ok": True,
                "status": "pending_confirmation",
                "fingerprint": session.fingerprint,
                "expires_in": max(0, int(session.expires_at - self._clock())),
            }
        return {
            "ok": True,
            "status": "paired",
            "fingerprint": session.fingerprint,
            **session.credentials,
        }

    def cleanup(self) -> None:
        now = self._clock()
        for session_id, session in list(self._sessions.items()):
            if session.expires_at <= now:
                self.cancel(session_id)

    @staticmethod
    def normalize_code(code: str) -> str:
        return "".join(character for character in str(code).upper() if character.isalnum())

    def _new_code(self) -> str:
        for _ in range(20):
            code = "".join(
                secrets.choice(PAIRING_ALPHABET)
                for _ in range(PAIRING_CODE_LENGTH)
            )
            if code not in self._codes:
                return code
        raise RuntimeError("Unable to allocate a unique pairing code")
