"""
OAuth2-Authentifizierung für die Gmail API.

Verwendet den OAuth2 "Installed App"-Flow:
  1. Beim ersten Start öffnet sich der Browser zur Google-Anmeldung
  2. Nach Zustimmung wird ein Token in 'config/token.json' gespeichert
  3. Bei weiteren Starts wird das Token automatisch erneuert

Voraussetzung:
  - OAuth2-Client-Credentials als 'config/credentials.json' im Projektordner
    (Download aus Google Cloud Console -> APIs & Services -> Credentials)

Verwendung:
    from gmail_bot.auth import get_gmail_service
    service = get_gmail_service()
    results = service.users().messages().list(userId="me").execute()
"""

from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gmail_bot.utils.logger import get_logger

logger = get_logger(__name__)

# ─── Konfiguration ─────────────────────────────────────────────────────────────

# Scopes bestimmen, auf welche Gmail-Funktionen zugegriffen werden darf.
# Bei Änderung der Scopes muss token.json gelöscht werden!
GMAIL_SCOPES = [
    "https://mail.google.com/",                         # Endgueltiges Loeschen
    "https://www.googleapis.com/auth/gmail.readonly",   # E-Mails lesen
    "https://www.googleapis.com/auth/gmail.modify",     # E-Mails ändern/löschen
    "https://www.googleapis.com/auth/gmail.send",       # E-Mails senden
]

# Pfade relativ zum Projektordner (gmail_automation_project/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_CREDENTIALS_FILE = _PROJECT_ROOT / "config" / "credentials.json"
_TOKEN_FILE = _PROJECT_ROOT / "config" / "token.json"


def _token_file_has_required_scopes() -> bool:
    """Prueft, ob das gespeicherte Token alle aktuell benoetigten Scopes nennt."""
    try:
        token_data = json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))
    except Exception:
        return False

    token_scopes = token_data.get("scopes")
    if not token_scopes:
        return False

    return set(GMAIL_SCOPES).issubset(set(token_scopes))


# ─── Authentifizierung ─────────────────────────────────────────────────────────

class AuthenticationError(Exception):
    """Fehler bei der OAuth2-Authentifizierung."""

    def __init__(self, message: str, *, reason: str = "unknown"):
        super().__init__(message)
        self.message = message
        self.reason = reason


def authenticate() -> Credentials:
    """
    Führt die OAuth2-Authentifizierung durch.

    1. Prüft, ob ein gültiges Token in config/token.json existiert
    2. Wenn abgelaufen -> automatischer Refresh
    3. Wenn kein Token -> startet den Browser-Login-Flow

    Returns:
        Gültige OAuth2 Credentials.

    Raises:
        AuthenticationError: Wenn credentials.json fehlt oder
                             die Authentifizierung fehlschlägt.
    """
    creds: Credentials | None = None

    # 1. Vorhandenes Token laden
    if _TOKEN_FILE.exists():
        try:
            if not _token_file_has_required_scopes():
                logger.warning(
                    "Gespeichertes Gmail-Token hat nicht alle benoetigten Scopes; "
                    "neue Autorisierung erforderlich."
                )
                creds = None
            else:
                creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), GMAIL_SCOPES)
                logger.debug("Token aus config/token.json geladen")
        except Exception as exc:
            logger.warning(f"token.json konnte nicht geladen werden: {exc}")
            creds = None

    # 2. Token erneuern oder neu holen
    if creds and creds.valid:
        logger.info("Gmail-Token ist gueltig")
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("Gmail-Token erfolgreich erneuert")
        except Exception as exc:
            logger.warning(f"Token-Refresh fehlgeschlagen: {exc} - starte neuen Login")
            creds = None

    if not creds:
        # 3. Neuer Login erforderlich
        if not _CREDENTIALS_FILE.exists():
            raise AuthenticationError(
                f"OAuth2 Credentials nicht gefunden: {_CREDENTIALS_FILE}\n"
                "Bitte 'credentials.json' aus der Google Cloud Console herunterladen:\n"
                "  -> APIs & Services -> Credentials -> OAuth 2.0 Client-IDs -> Download JSON\n"
                "  -> Speichern unter: config/credentials.json",
                reason="credentials_file_missing",
            )

        try:
            logger.info("Starte OAuth2-Login im Browser...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_CREDENTIALS_FILE), GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
            logger.info("OAuth2-Login erfolgreich abgeschlossen")
        except Exception as exc:
            raise AuthenticationError(
                f"OAuth2-Login fehlgeschlagen: {exc}",
                reason="oauth_flow_failed",
            ) from exc

    # 4. Token speichern für nächsten Start
    try:
        _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_FILE.write_text(creds.to_json())
        logger.info(f"Token gespeichert in: {_TOKEN_FILE}")
    except Exception as exc:
        logger.warning(f"Token konnte nicht gespeichert werden: {exc}")

    return creds


# ─── Gmail Service erstellen ──────────────────────────────────────────────────

def get_gmail_service():
    """
    Erstellt und gibt einen authentifizierten Gmail API Service zurueck.

    Returns:
        googleapiclient.discovery.Resource: Gmail API Service-Objekt.

    Beispiel::
        service = get_gmail_service()
        messages = service.users().messages().list(userId="me").execute()
    """
    creds = authenticate()
    service = build("gmail", "v1", credentials=creds)
    logger.info("Gmail API Service erstellt")
    return service
