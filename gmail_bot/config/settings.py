"""
Zentrale Konfiguration fuer das Gmail Automation Projekt.

Liest Einstellungen aus Umgebungsvariablen (.env) und stellt
sie als typsicheres Pydantic-Settings-Objekt bereit.

Verwendung:
    from gmail_bot.config import get_settings
    settings = get_settings()
    print(settings.google_cloud_project)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# .env aus dem Projektordner laden
_PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


# ─── Konstanten ────────────────────────────────────────────────────────────────

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
)


# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _parse_csv(value: str | None, fallback: tuple[str, ...]) -> tuple[str, ...]:
    """Parst eine kommaseparierte Umgebungsvariable in ein Tuple."""
    if not value:
        return fallback
    parts = tuple(part.strip() for part in value.split(",") if part.strip())
    return parts or fallback


# ─── Settings ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Settings:
    """Zentrale, unveraenderliche Konfiguration."""

    google_cloud_project: str
    gmail_user: str
    max_results: int
    log_level: str
    cors_origins: tuple[str, ...]


@lru_cache
def get_settings() -> Settings:
    """
    Erstellt und cached die Settings aus Umgebungsvariablen.

    Umgebungsvariablen:
        GOOGLE_CLOUD_PROJECT: Google Cloud Projekt-ID
        GMAIL_USER:           Gmail-Adresse (Standard: "me")
        MAX_RESULTS:          Standard-Anzahl Ergebnisse (Standard: 20)
        LOG_LEVEL:            Log-Level (Standard: DEBUG)
        FRONTEND_ORIGINS:     Kommaseparierte CORS Origins
    """
    return Settings(
        google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
        gmail_user=os.getenv("GMAIL_USER", "me"),
        max_results=int(os.getenv("MAX_RESULTS", "20")),
        log_level=os.getenv("LOG_LEVEL", "DEBUG").upper(),
        cors_origins=_parse_csv(
            os.getenv("FRONTEND_ORIGINS"),
            fallback=DEFAULT_CORS_ORIGINS,
        ),
    )
