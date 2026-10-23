"""
Erweiterte Exception-Hierarchie für besseres Error-Handling.

Kategorisiert Fehler nach Typ für gezieltes Error-Handling:
  - GmailAPIError: Fehler von der Gmail API
  - AuthenticationError: Authentifizierungs-Probleme
  - ValidationError: Validierungs-Fehler
  - RateLimitError: API Rate-Limit überschritten
  - MessageNotFoundError: E-Mail nicht gefunden

Verwendung:
    from gmail_bot.core.exceptions import GmailAPIError, RateLimitError

    try:
        client.send_message(...)
    except RateLimitError:
        logger.info("Rate-Limit erreicht, bitte warten...")
    except ValidationError as e:
        logger.error(f"Ungültige Eingabe: {e.details}")
    except GmailAPIError as e:
        logger.error(f"API-Fehler: {e.reason}")
"""

from __future__ import annotations

from typing import Any, Optional


class GmailBotError(Exception):
    """Basis-Exception für alle Gmail Bot Fehler."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unknown",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Args:
            message: Benutzerfreundliche Fehlermeldung.
            reason: Fehler-Kategorie (für strukturiertes Logging).
            details: Zusätzliche Fehler-Details als Dict.
        """
        super().__init__(message)
        self.message = message
        self.reason = reason
        self.details = details or {}

    def __str__(self) -> str:
        """Gibt eine formatierte Fehlermeldung zurück."""
        result = f"{self.__class__.__name__}: {self.message}"
        if self.reason != "unknown":
            result += f" ({self.reason})"
        return result


class GmailAPIError(GmailBotError):
    """Fehler von der Gmail API."""

    pass


class AuthenticationError(GmailBotError):
    """Fehler bei der OAuth2-Authentifizierung."""

    pass


class ValidationError(GmailBotError):
    """Fehler bei der Input-Validierung."""

    pass


class RateLimitError(GmailBotError):
    """Gmail API Rate-Limit überschritten."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: int = 60,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Args:
            message: Benutzerfreundliche Fehlermeldung.
            retry_after: Empfohlene Wartezeit in Sekunden.
            details: Zusätzliche Fehler-Details.
        """
        super().__init__(message, reason="rate_limit", details=details or {})
        self.retry_after = retry_after

    def __str__(self) -> str:
        return f"{super().__str__()} [Bitte warten Sie {self.retry_after}s]"


class MessageNotFoundError(GmailBotError):
    """E-Mail nicht gefunden."""

    def __init__(self, message_id: str):
        super().__init__(
            f"E-Mail nicht gefunden: {message_id}",
            reason="message_not_found",
            details={"message_id": message_id},
        )


class LabelNotFoundError(GmailBotError):
    """Label nicht gefunden."""

    def __init__(self, label_id: str):
        super().__init__(
            f"Label nicht gefunden: {label_id}",
            reason="label_not_found",
            details={"label_id": label_id},
        )


class NetworkError(GmailBotError):
    """Netzwerk-Fehler (Verbindungsprobleme, Timeouts)."""

    pass


class InvalidConfigError(GmailBotError):
    """Fehler in der Konfiguration."""

    pass


# Exception-Mapper für Gmail API Fehler
def map_google_error_to_gmail_error(exc: Exception) -> GmailBotError:
    """
    Konvertiert Google API-Fehler zu typsicheren Gmail Bot Errors.

    Args:
        exc: Die ursprüngliche Google API Exception.

    Returns:
        Entsprechende GmailBotError-Subclass.
    """
    error_str = str(exc).lower()

    # Rate Limit Fehler
    if "rate_limit" in error_str or "quotaexceeded" in error_str:
        return RateLimitError(
            f"Gmail API Rate-Limit erreicht: {exc}",
            retry_after=60,
        )

    # Authentifizierungs-Fehler
    if "unauthorized" in error_str or "authentication" in error_str:
        return AuthenticationError(f"Authentifizierung fehlgeschlagen: {exc}")

    # Netzwerk-Fehler
    if "connection" in error_str or "timeout" in error_str or "network" in error_str:
        return NetworkError(f"Netzwerkfehler: {exc}")

    # 404 Not Found
    if "404" in error_str or "not found" in error_str:
        return MessageNotFoundError(getattr(exc, "message_id", "unknown"))

    # Allgemeiner API-Fehler
    return GmailAPIError(f"Gmail API Fehler: {exc}")
