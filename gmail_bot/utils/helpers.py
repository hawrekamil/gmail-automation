"""Hilfsfunktionen fuer das Gmail Bot Projekt."""

from __future__ import annotations

import base64


def truncate(text: str, max_length: int = 80) -> str:
    """Kuerzt einen Text auf die angegebene Laenge."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def safe_decode_base64(data: str) -> str:
    """Dekodiert Base64 URL-safe Daten zu einem UTF-8 String."""
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8")
    except Exception:
        return ""
