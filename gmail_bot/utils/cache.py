"""
Einfaches TTL-basiertes Caching für häufige API-Abfragen.

Wird verwendet für:
  - Labels (ändern selten)
  - Profil-Informationen (ändern selten)
  - Häufige Queries (kurze TTL)

Verwendung:
    from gmail_bot.utils.cache import CacheManager

    cache = CacheManager()
    cache.set("my_key", {"data": "value"}, ttl=300)
    data = cache.get("my_key")
"""

from __future__ import annotations

import time
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class CacheEntry(Generic[T]):
    """Speichert einen Cache-Eintrag mit TTL."""

    def __init__(self, value: T, ttl: int):
        """
        Args:
            value: Der zu cachende Wert.
            ttl: Time-to-live in Sekunden.
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Prüft, ob der Cache-Eintrag abgelaufen ist."""
        return time.time() - self.created_at > self.ttl


class CacheManager:
    """
    Einfacher In-Memory Cache mit TTL-Verwaltung.

    Nicht thread-safe – für Multi-Threading Lock verwenden.
    """

    def __init__(self):
        self._store: dict[str, CacheEntry[Any]] = {}

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Speichert einen Wert im Cache.

        Args:
            key: Cache-Schlüssel.
            value: Der zu cachende Wert.
            ttl: Time-to-live in Sekunden (default: 5 Min).
        """
        self._store[key] = CacheEntry(value, ttl)

    def get(self, key: str) -> Any | None:
        """
        Ruft einen Wert aus dem Cache ab.

        Args:
            key: Cache-Schlüssel.

        Returns:
            Der gecachte Wert oder None, falls abgelaufen/nicht vorhanden.
        """
        if key not in self._store:
            return None

        entry = self._store[key]
        if entry.is_expired():
            del self._store[key]
            return None

        return entry.value

    def clear(self, key: str | None = None) -> None:
        """
        Löscht einen oder alle Cache-Einträge.

        Args:
            key: Optionaler Schlüssel. Wenn None, wird der komplette Cache geleert.
        """
        if key is None:
            self._store.clear()
        elif key in self._store:
            del self._store[key]

    def size(self) -> int:
        """Gibt die Anzahl gültiger Cache-Einträge zurück."""
        # Bereinige abgelaufene Einträge
        expired_keys = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired_keys:
            del self._store[k]
        return len(self._store)


# Globale Instanz für Verwendung im Projekt
_global_cache = CacheManager()


def get_cache_manager() -> CacheManager:
    """Gibt die globale Cache-Instanz zurück."""
    return _global_cache
