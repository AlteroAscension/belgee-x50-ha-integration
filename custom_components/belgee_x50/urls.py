"""URL handling that does not depend on Home Assistant runtime imports."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def normalize_public_base_url(value: str) -> str:
    """Validate and normalize the externally reachable Home Assistant URL."""
    raw = value.strip()
    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a complete http:// or https:// URL")
    if parsed.query or parsed.fragment:
        raise ValueError(
            "The public Home Assistant URL cannot contain query or fragment"
        )
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))
