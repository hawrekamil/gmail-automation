"""
Pydantic Datenmodelle fuer typsichere E-Mail-Verarbeitung.

Diese Modelle werden sowohl intern (Service-Layer) als auch extern
(API-Responses) verwendet und stellen sicher, dass Daten immer
validiert und konsistent sind.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EmailSummary:
    """Kompakte E-Mail-Uebersicht (fuer Listenansichten)."""

    id: str
    thread_id: str = ""
    subject: str = "(kein Betreff)"
    sender: str = ""
    to: str = ""
    date: str = ""
    snippet: str = ""
    label_ids: list[str] = field(default_factory=list)
    is_unread: bool = False

    @classmethod
    def from_api(cls, data: dict) -> EmailSummary:
        """Erstellt eine EmailSummary aus einem Gmail API Dictionary."""
        return cls(
            id=data.get("id", ""),
            thread_id=data.get("thread_id", ""),
            subject=data.get("subject", "(kein Betreff)"),
            sender=data.get("from", ""),
            to=data.get("to", ""),
            date=data.get("date", ""),
            snippet=data.get("snippet", ""),
            label_ids=data.get("label_ids", []),
            is_unread=data.get("is_unread", False),
        )


@dataclass
class EmailDetail(EmailSummary):
    """Vollstaendige E-Mail mit Body (fuer Detailansicht)."""

    body: str = ""
    cc: str = ""

    @classmethod
    def from_api(cls, data: dict) -> EmailDetail:
        """Erstellt ein EmailDetail aus einem Gmail API Dictionary."""
        return cls(
            id=data.get("id", ""),
            thread_id=data.get("thread_id", ""),
            subject=data.get("subject", "(kein Betreff)"),
            sender=data.get("from", ""),
            to=data.get("to", ""),
            cc=data.get("cc", ""),
            date=data.get("date", ""),
            body=data.get("body", ""),
            snippet=data.get("snippet", ""),
            label_ids=data.get("label_ids", []),
            is_unread=data.get("is_unread", False),
        )


@dataclass
class SendEmailRequest:
    """Request-Modell zum Senden einer E-Mail."""

    to: str
    subject: str
    body: str
    cc: str = ""
    html: bool = False

    def validate(self) -> None:
        """Validiert die Pflichtfelder."""
        if not self.to or not self.to.strip():
            raise ValueError("Empfaenger (to) darf nicht leer sein.")
        if not self.subject or not self.subject.strip():
            raise ValueError("Betreff (subject) darf nicht leer sein.")
