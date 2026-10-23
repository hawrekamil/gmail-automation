"""
Gmail API Kernklasse – alle direkten API-Aufrufe.

Kapselt die Gmail API und bietet typsichere Methoden fuer:
  - E-Mails auflisten (mit Suchfilter)
  - E-Mail lesen (Volltext mit Body-Extraktion)
  - E-Mail senden (Plain Text / HTML)
  - E-Mail loeschen (Papierkorb / endgueltig)
  - Labels verwalten
  - Profil abrufen

Verwendung:
    from gmail_bot.core import GmailClient

    client = GmailClient()
    emails = client.list_messages(max_results=10)
    email  = client.get_message("message_id_123")
    client.send_message("empfaenger@example.com", "Betreff", "Nachricht")
    client.trash_message("message_id_123")
"""

from __future__ import annotations

import base64
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from email.mime.text import MIMEText
from typing import Any

from gmail_bot.auth import get_gmail_service
from gmail_bot.utils.logger import get_logger

logger = get_logger(__name__)
_thread_local = threading.local()


def _get_metadata_worker_count() -> int:
    """Liest die Worker-Anzahl fuer paralleles Metadatenladen."""
    try:
        return min(max(int(os.getenv("GMAIL_METADATA_WORKERS", "4")), 1), 8)
    except ValueError:
        logger.warning("Ungueltiger Wert fuer GMAIL_METADATA_WORKERS; verwende 4")
        return 4


class GmailClient:
    """
    Kernklasse fuer alle Gmail API-Aufrufe.

    Stellt eine duenne, typsichere Schicht ueber der Gmail API bereit.
    Fuer hoehere Automatisierungs-Workflows siehe ``gmail_bot.services.email_service``.
    """

    def __init__(self):
        self._service = get_gmail_service()
        self._user_id = "me"
        self._metadata_workers = _get_metadata_worker_count()

    def _get_metadata_service(self):
        """Gibt pro Thread eine eigene Gmail-Service-Instanz zurueck."""
        if self._metadata_workers == 1:
            return self._service

        service = getattr(_thread_local, "gmail_service", None)
        if service is None:
            service = get_gmail_service()
            _thread_local.gmail_service = service
        return service

    # ─── E-Mails auflisten ────────────────────────────────────────────────────

    def list_messages(
        self,
        max_results: int = 20,
        query: str = "",
        label_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Listet E-Mail-Metadaten auf.

        Args:
            max_results: Maximale Anzahl der Ergebnisse (1-100).
            query: Gmail-Suchfilter (z.B. "is:unread", "from:boss@firma.de").
            label_ids: Label-Filter (z.B. ["INBOX"], ["UNREAD"]).

        Returns:
            Liste mit E-Mail-Uebersichten (id, subject, from, date, snippet).
        """
        params: dict[str, Any] = {
            "userId": self._user_id,
            "maxResults": min(max(max_results, 1), 500),
            "fields": "messages(id,threadId),nextPageToken",
        }
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids

        result = self._service.users().messages().list(**params).execute()
        messages = result.get("messages", [])

        if not messages:
            logger.info("Keine E-Mails gefunden", extra={"query": query})
            return []

        worker_count = min(self._metadata_workers, len(messages))
        if worker_count == 1:
            email_list = [
                email
                for email in (self._fetch_message_metadata(msg["id"]) for msg in messages)
                if email is not None
            ]
        else:
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                email_list = [
                    email
                    for email in executor.map(
                        self._fetch_message_metadata,
                        (msg["id"] for msg in messages),
                    )
                    if email is not None
                ]

        logger.info(
            f"{len(email_list)} E-Mails geladen",
            extra={"query": query, "count": len(email_list)},
        )
        return email_list

    def _fetch_message_metadata(self, message_id: str) -> dict[str, Any] | None:
        """Laedt Metadaten fuer eine E-Mail."""
        try:
            service = self._get_metadata_service()
            detail = service.users().messages().get(
                userId=self._user_id,
                id=message_id,
                format="metadata",
                metadataHeaders=["Subject", "From", "Date", "To"],
                fields="id,threadId,labelIds,snippet,payload/headers",
            ).execute()

            headers = {
                h["name"]: h["value"]
                for h in detail.get("payload", {}).get("headers", [])
            }

            return {
                "id": detail["id"],
                "thread_id": detail.get("threadId"),
                "subject": headers.get("Subject", "(kein Betreff)"),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "snippet": detail.get("snippet", ""),
                "label_ids": detail.get("labelIds", []),
                "is_unread": "UNREAD" in detail.get("labelIds", []),
            }
        except Exception as exc:
            logger.warning(f"E-Mail {message_id} konnte nicht geladen werden: {exc}")
            return None

    def list_all_message_ids(
        self,
        query: str = "",
        label_ids: list[str] | None = None,
        page_size: int = 500,
    ) -> list[str]:
        """
        Listet alle Message-IDs passend zu Query/Labels ueber alle Gmail-Seiten.

        Args:
            query: Gmail-Suchfilter.
            label_ids: Label-Filter.
            page_size: Anzahl pro API-Seite (max. 500).

        Returns:
            Liste aller gefundenen Gmail Message-IDs.
        """
        params: dict[str, Any] = {
            "userId": self._user_id,
            "maxResults": min(max(page_size, 1), 500),
            "fields": "messages/id,nextPageToken",
        }
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids

        message_ids: list[str] = []
        while True:
            result = self._service.users().messages().list(**params).execute()
            message_ids.extend(msg["id"] for msg in result.get("messages", []))

            next_page_token = result.get("nextPageToken")
            if not next_page_token:
                break
            params["pageToken"] = next_page_token

        logger.info(
            f"{len(message_ids)} E-Mail-IDs geladen",
            extra={"query": query, "label_ids": label_ids, "count": len(message_ids)},
        )
        return message_ids

    # ─── E-Mail lesen (Volltext) ──────────────────────────────────────────────

    def get_message(self, message_id: str) -> dict[str, Any]:
        """
        Liest den vollstaendigen Inhalt einer E-Mail.

        Args:
            message_id: Die ID der Nachricht.

        Returns:
            Dictionary mit allen E-Mail-Details (headers, body).
        """
        message = self._service.users().messages().get(
            userId=self._user_id,
            id=message_id,
            format="full",
            fields="id,threadId,labelIds,snippet,payload",
        ).execute()

        headers = {
            h["name"]: h["value"]
            for h in message.get("payload", {}).get("headers", [])
        }

        body = self._extract_body(message.get("payload", {}))

        result = {
            "id": message["id"],
            "thread_id": message.get("threadId"),
            "subject": headers.get("Subject", "(kein Betreff)"),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "cc": headers.get("Cc", ""),
            "date": headers.get("Date", ""),
            "body": body,
            "snippet": message.get("snippet", ""),
            "label_ids": message.get("labelIds", []),
            "is_unread": "UNREAD" in message.get("labelIds", []),
        }

        logger.info(
            f"E-Mail gelesen: {result['subject'][:50]}",
            extra={"message_id": message_id},
        )
        return result

    # ─── E-Mail senden ────────────────────────────────────────────────────────

    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        html: bool = False,
    ) -> dict[str, str]:
        """
        Sendet eine neue E-Mail.

        Args:
            to: Empfaenger-Adresse.
            subject: Betreff der E-Mail.
            body: Nachrichtentext (plain text oder HTML).
            cc: CC-Empfaenger (optional).
            html: True = HTML-E-Mail, False = Plain Text.

        Returns:
            Dictionary mit der gesendeten Nachrichten-ID.
        """
        mime_type = "html" if html else "plain"
        message = MIMEText(body, mime_type, "utf-8")
        message["to"] = to
        message["subject"] = subject
        if cc:
            message["cc"] = cc

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        sent = self._service.users().messages().send(
            userId=self._user_id,
            body={"raw": raw},
        ).execute()

        logger.info(
            f"E-Mail gesendet an: {to}",
            extra={"message_id": sent.get("id"), "to": to, "subject": subject},
        )

        return {
            "id": sent.get("id", ""),
            "thread_id": sent.get("threadId", ""),
            "message": f"E-Mail erfolgreich gesendet an {to}",
        }

    # ─── E-Mail loeschen ──────────────────────────────────────────────────────

    def trash_message(self, message_id: str) -> dict[str, str]:
        """Verschiebt eine E-Mail in den Papierkorb."""
        self._service.users().messages().trash(
            userId=self._user_id,
            id=message_id,
        ).execute()

        logger.info("E-Mail in Papierkorb verschoben", extra={"message_id": message_id})
        return {"message_id": message_id, "message": "E-Mail in den Papierkorb verschoben."}

    def delete_message(self, message_id: str) -> dict[str, str]:
        """Loescht eine E-Mail endgueltig (unwiderruflich!)."""
        self._service.users().messages().delete(
            userId=self._user_id,
            id=message_id,
        ).execute()

        logger.info("E-Mail endgueltig geloescht", extra={"message_id": message_id})
        return {"message_id": message_id, "message": "E-Mail endgueltig geloescht."}

    # ─── Labels ───────────────────────────────────────────────────────────────

    def list_labels(self) -> list[dict[str, str]]:
        """Gibt alle Gmail-Labels zurueck."""
        result = self._service.users().labels().list(
            userId=self._user_id,
            fields="labels(id,name)",
        ).execute()
        labels = result.get("labels", [])
        logger.info(f"{len(labels)} Labels geladen")
        return [{"id": l["id"], "name": l["name"]} for l in labels]

    def create_label(self, name: str) -> dict[str, str]:
        """Erstellt ein neues Label."""
        body = {
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        }
        result = self._service.users().labels().create(
            userId=self._user_id,
            body=body
        ).execute()
        logger.info(f"Label erstellt: {name}")
        return {"id": result["id"], "name": result["name"]}

    def rename_label(self, label_id: str, new_name: str) -> dict[str, str]:
        """Benennt ein Label um."""
        body = {
            "name": new_name
        }
        result = self._service.users().labels().patch(
            userId=self._user_id,
            id=label_id,
            body=body
        ).execute()
        logger.info(f"Label umbenannt: {new_name}")
        return {"id": result["id"], "name": result["name"]}

    def modify_labels(
        self,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fuegt Labels hinzu oder entfernt sie von einer E-Mail."""
        body: dict[str, list[str]] = {}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels

        result = self._service.users().messages().modify(
            userId=self._user_id,
            id=message_id,
            body=body,
        ).execute()

        logger.info(
            "Labels aktualisiert",
            extra={"message_id": message_id, "add": add_labels, "remove": remove_labels},
        )
        return result

    def mark_as_read(self, message_id: str) -> dict[str, Any]:
        """Markiert eine E-Mail als gelesen."""
        return self.modify_labels(message_id, remove_labels=["UNREAD"])

    def mark_as_unread(self, message_id: str) -> dict[str, Any]:
        """Markiert eine E-Mail als ungelesen."""
        return self.modify_labels(message_id, add_labels=["UNREAD"])

    # ─── Profil ───────────────────────────────────────────────────────────────

    def get_profile(self) -> dict[str, Any]:
        """Gibt das Gmail-Profil des authentifizierten Benutzers zurueck."""
        profile = self._service.users().getProfile(
            userId=self._user_id,
            fields="emailAddress,messagesTotal,threadsTotal",
        ).execute()
        return {
            "email": profile.get("emailAddress"),
            "messages_total": profile.get("messagesTotal"),
            "threads_total": profile.get("threadsTotal"),
        }

    # ─── Volltextsuche ────────────────────────────────────────────────────────

    def fulltext_search(
        self,
        search_term: str,
        max_results: int = 50,
        label_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Durchsucht E-Mail-Bodies nach einem Suchbegriff.

        Nutzt Gmails q-Parameter fuer die Vorfilterung und laedt anschliessend
        den vollstaendigen Body, um exakte Treffer zu garantieren.

        Args:
            search_term: Der Suchbegriff (Gross/Kleinschreibung wird ignoriert).
            max_results: Maximale Anzahl der Ergebnisse (1-100).
            label_ids: Optionale Label-Filter.

        Returns:
            Liste mit E-Mail-Details (id, subject, from, date, body, match_context).
        """
        # Phase 1: Gmail-Vorfilterung mit q-Parameter
        params: dict[str, Any] = {
            "userId": self._user_id,
            "maxResults": min(max(max_results * 2, 10), 500),  # Mehr laden wegen Client-Filter
            "fields": "messages(id),nextPageToken",
            "q": search_term,
        }
        if label_ids:
            params["labelIds"] = label_ids

        result = self._service.users().messages().list(**params).execute()
        messages = result.get("messages", [])

        if not messages:
            logger.info("Volltextsuche: Keine Treffer", extra={"search_term": search_term})
            return []

        # Phase 2: Bodies laden und exakt filtern
        search_lower = search_term.lower()
        matches: list[dict[str, Any]] = []

        worker_count = min(self._metadata_workers, len(messages))

        def _check_message(msg_id: str) -> dict[str, Any] | None:
            """Laedt den Body und prueft auf exakten Treffer."""
            try:
                service = self._get_metadata_service()
                detail = service.users().messages().get(
                    userId=self._user_id,
                    id=msg_id,
                    format="full",
                    fields="id,threadId,labelIds,snippet,payload",
                ).execute()

                headers = {
                    h["name"]: h["value"]
                    for h in detail.get("payload", {}).get("headers", [])
                }

                body = self._extract_body(detail.get("payload", {}))
                subject = headers.get("Subject", "(kein Betreff)")

                # Exakter Treffer im Body, Betreff oder Snippet?
                body_lower = body.lower()
                subject_lower = subject.lower()
                snippet_lower = detail.get("snippet", "").lower()

                if search_lower not in body_lower and search_lower not in subject_lower and search_lower not in snippet_lower:
                    return None

                # Match-Kontext extrahieren (Umgebungstext um den Treffer)
                match_context = ""
                for text in [body, subject, detail.get("snippet", "")]:
                    pos = text.lower().find(search_lower)
                    if pos >= 0:
                        start = max(0, pos - 60)
                        end = min(len(text), pos + len(search_term) + 60)
                        prefix = "..." if start > 0 else ""
                        suffix = "..." if end < len(text) else ""
                        match_context = prefix + text[start:end].strip() + suffix
                        break

                return {
                    "id": detail["id"],
                    "thread_id": detail.get("threadId"),
                    "subject": subject,
                    "from": headers.get("From", ""),
                    "to": headers.get("To", ""),
                    "date": headers.get("Date", ""),
                    "snippet": detail.get("snippet", ""),
                    "body": body,
                    "label_ids": detail.get("labelIds", []),
                    "is_unread": "UNREAD" in detail.get("labelIds", []),
                    "match_context": match_context,
                }
            except Exception as exc:
                logger.warning(f"Volltextsuche: E-Mail {msg_id} konnte nicht geladen werden: {exc}")
                return None

        if worker_count <= 1:
            for msg in messages:
                hit = _check_message(msg["id"])
                if hit:
                    matches.append(hit)
                if len(matches) >= max_results:
                    break
        else:
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                for hit in executor.map(_check_message, (msg["id"] for msg in messages)):
                    if hit:
                        matches.append(hit)
                    if len(matches) >= max_results:
                        break

        logger.info(
            f"Volltextsuche: {len(matches)} exakte Treffer",
            extra={"search_term": search_term, "candidates": len(messages), "matches": len(matches)},
        )
        return matches

    # ─── Hilfsmethoden ────────────────────────────────────────────────────────

    def _extract_body(self, payload: dict) -> str:
        """Extrahiert den E-Mail-Body aus der Gmail API Payload-Struktur."""
        body = ""

        if "body" in payload and payload["body"].get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        elif "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(
                        part["body"]["data"]
                    ).decode("utf-8")
                    break
                elif mime_type == "text/html" and not body:
                    if part.get("body", {}).get("data"):
                        body = base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8")
                # Verschachtelte Parts (z.B. multipart/alternative)
                elif "parts" in part:
                    body = self._extract_body(part)
                    if body:
                        break

        return body
