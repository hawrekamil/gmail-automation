"""
E-Mail Service – Fertige Automatisierungs-Workflows.

Baut auf dem GmailClient (core) auf und bietet hoehere Funktionen
wie typsichere E-Mail-Operationen, Batch-Verarbeitung und
vorbereitete Automatisierungs-Workflows.

Verwendung:
    from gmail_bot.services import EmailService

    service = EmailService()
    emails = service.get_inbox(max_results=5)
    service.send("user@example.com", "Betreff", "Nachricht")
    
    # Batch-Operationen
    processor = service.get_batch_processor()
    result = processor.mark_as_read([msg_id_1, msg_id_2, ...])
"""

from __future__ import annotations

from gmail_bot.core import GmailClient
from gmail_bot.models import EmailSummary, EmailDetail, SendEmailRequest
from gmail_bot.services.batch_processor import BatchProcessor
from gmail_bot.utils.cache import get_cache_manager
from gmail_bot.utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """
    High-Level E-Mail-Service mit typsicheren Modellen.

    Nutzt intern den GmailClient fuer API-Aufrufe und gibt
    typsichere Datenmodelle zurueck statt roher Dictionaries.
    
    Features:
      - Typsichere Datenmodelle
      - Caching für Labels und Profile
      - Batch-Operationen für mehrere E-Mails
    """

    def __init__(self):
        self._client = GmailClient()
        self._cache = get_cache_manager()
        self._batch_processor = BatchProcessor(self._client._service)

    # ─── Lesen ────────────────────────────────────────────────────────────────

    def get_inbox(
        self,
        max_results: int = 20,
        query: str = "",
    ) -> list[EmailSummary]:
        """
        Holt E-Mails aus dem Posteingang.

        Args:
            max_results: Maximale Anzahl (1-100).
            query: Gmail-Suchfilter.

        Returns:
            Liste typsicherer EmailSummary-Objekte.
        """
        raw_emails = self._client.list_messages(
            max_results=max_results,
            query=query,
            label_ids=["INBOX"],
        )
        return [EmailSummary.from_api(e) for e in raw_emails]

    def get_unread(self, max_results: int = 20) -> list[EmailSummary]:
        """Holt nur ungelesene E-Mails."""
        return self.get_inbox(max_results=max_results, query="is:unread")

    def read_email(self, message_id: str) -> EmailDetail:
        """
        Liest eine vollstaendige E-Mail.

        Args:
            message_id: Die Gmail Message-ID.

        Returns:
            Typsicheres EmailDetail-Objekt mit Body.
        """
        raw = self._client.get_message(message_id)
        return EmailDetail.from_api(raw)

    def get_all_message_ids(
        self,
        label_id: str,
        query: str = "",
    ) -> list[str]:
        """Gibt alle Message-IDs in einem Label/Ordner zurueck."""
        return self._client.list_all_message_ids(query=query, label_ids=[label_id])

    def search_emails(
        self,
        query: str = "",
        max_results: int = 50,
        label_ids: list[str] | None = None,
    ) -> list[EmailSummary]:
        """
        Sucht E-Mails anhand einer Gmail-Query.

        Args:
            query: Gmail-Suchfilter.
            max_results: Maximale Anzahl (1-500).
            label_ids: Optionale Label-Filter.

        Returns:
            Liste typsicherer EmailSummary-Objekte.
        """
        raw = self._client.list_messages(
            max_results=max_results,
            query=query,
            label_ids=label_ids or [],
        )
        return [EmailSummary.from_api(e) for e in raw]

    def get_email_previews(
        self,
        max_results: int = 5,
        query: str = "",
        label_ids: list[str] | None = None,
    ) -> list[EmailSummary]:
        """
        Gibt eine kurze Vorschau-Liste von E-Mails zurueck.

        Args:
            max_results: Maximale Anzahl (default: 5).
            query: Gmail-Suchfilter.
            label_ids: Optionale Label-Filter.

        Returns:
            Liste typsicherer EmailSummary-Objekte.
        """
        raw = self._client.list_messages(
            max_results=max_results,
            query=query,
            label_ids=label_ids or [],
        )
        return [EmailSummary.from_api(e) for e in raw]

    def get_email(self, message_id: str) -> dict:
        """
        Holt rohe E-Mail-Daten (Metadaten) fuer eine einzelne E-Mail.

        Args:
            message_id: Die Gmail Message-ID.

        Returns:
            Rohes Dictionary mit Metadaten.
        """
        raw = self._client.list_messages(max_results=1, query=f"rfc822msgid:{message_id}")
        if raw:
            return raw[0]
        return {}

    # ─── Senden ───────────────────────────────────────────────────────────────

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        html: bool = False,
    ) -> dict[str, str]:
        """
        Sendet eine E-Mail mit Validierung.

        Args:
            to: Empfaenger.
            subject: Betreff.
            body: Nachrichtentext.
            cc: CC-Empfaenger (optional).
            html: HTML-Format (optional).

        Returns:
            Bestaetigung mit Message-ID.
        """
        request = SendEmailRequest(to=to, subject=subject, body=body, cc=cc, html=html)
        request.validate()

        return self._client.send_message(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            html=request.html,
        )

    # ─── Loeschen ─────────────────────────────────────────────────────────────

    def trash(self, message_id: str) -> dict[str, str]:
        """Verschiebt eine E-Mail in den Papierkorb."""
        return self._client.trash_message(message_id)

    def delete_permanently(self, message_id: str) -> dict[str, str]:
        """Loescht eine E-Mail endgueltig."""
        return self._client.delete_message(message_id)

    # ─── Labels ───────────────────────────────────────────────────────────────

    def mark_as_read(self, message_id: str) -> None:
        """Markiert eine E-Mail als gelesen."""
        self._client.mark_as_read(message_id)
        logger.info(f"E-Mail als gelesen markiert: {message_id}")

    def get_labels(self, use_cache: bool = True) -> list[dict[str, str]]:
        """
        Gibt alle verfuegbaren Labels zurueck.
        
        Args:
            use_cache: Wenn True, verwendet gecachte Labels (TTL: 10 Min).
        
        Returns:
            Liste der Labels.
        """
        if use_cache:
            cached = self._cache.get("labels")
            if cached is not None:
                logger.debug("Labels aus Cache geladen")
                return cached
        
        labels = self._client.list_labels()
        if use_cache:
            self._cache.set("labels", labels, ttl=600)  # 10 Minuten
        return labels

    def create_label(self, name: str) -> dict[str, str]:
        """Erstellt ein neues Label und leert den Cache."""
        result = self._client.create_label(name)
        self.clear_cache()
        return result

    def rename_label(self, label_id: str, new_name: str) -> dict[str, str]:
        """Benennt ein Label um und leert den Cache."""
        result = self._client.rename_label(label_id, new_name)
        self.clear_cache()
        return result

    # ─── Profil ───────────────────────────────────────────────────────────────

    def get_profile(self, use_cache: bool = True) -> dict:
        """
        Gibt das Gmail-Profil zurueck.
        
        Args:
            use_cache: Wenn True, verwendet gecachtes Profil (TTL: 30 Min).
        
        Returns:
            Profil-Dictionary.
        """
        if use_cache:
            cached = self._cache.get("profile")
            if cached is not None:
                logger.debug("Profil aus Cache geladen")
                return cached
        
        profile = self._client.get_profile()
        if use_cache:
            self._cache.set("profile", profile, ttl=1800)  # 30 Minuten
        return profile

    # ─── Batch-Operationen ────────────────────────────────────────────────────

    def get_batch_processor(self) -> BatchProcessor:
        """
        Gibt den Batch-Processor für Operationen auf mehreren E-Mails zurück.
        
        Returns:
            BatchProcessor-Instanz.
        
        Beispiel:
            processor = service.get_batch_processor()
            result = processor.mark_as_read([msg_id_1, msg_id_2])
            print(f"Erfolg: {result.success}/{result.total}")
        """
        return self._batch_processor

    def batch_mark_as_read(self, message_ids: list[str]) -> dict:
        """
        Markiert mehrere E-Mails als gelesen (Batch-Operation).
        
        Args:
            message_ids: Liste von Message-IDs.
        
        Returns:
            Statistik-Dictionary mit success/failed/total.
        """
        result = self._batch_processor.mark_as_read(message_ids)
        logger.info(f"Batch Mark-As-Read: {result}")
        return {
            "total": result.total,
            "success": result.success,
            "failed": result.failed,
            "success_rate": result.success_rate,
            "errors": result.errors,
        }

    def batch_apply_label(self, message_ids: list[str], label_id: str) -> dict:
        """
        Wendet ein Label auf mehrere E-Mails an (Batch-Operation).
        
        Args:
            message_ids: Liste von Message-IDs.
            label_id: Die ID des anzuwendenden Labels.
        
        Returns:
            Statistik-Dictionary mit success/failed/total.
        """
        result = self._batch_processor.apply_label(message_ids, label_id)
        logger.info(f"Batch Apply Label: {result}")
        return {
            "total": result.total,
            "success": result.success,
            "failed": result.failed,
            "success_rate": result.success_rate,
            "errors": result.errors,
        }

    def batch_move_to_label(self, message_ids: list[str], add_label_id: str, remove_label_id: str) -> dict:
        """
        Verschiebt mehrere E-Mails in ein neues Label und entfernt das alte (Batch-Operation).
        """
        result = self._batch_processor.move_messages(message_ids, add_label_id, remove_label_id)
        logger.info(f"Batch Move to Label: {result}")
        return {
            "total": result.total,
            "success": result.success,
            "failed": result.failed,
            "success_rate": result.success_rate,
            "errors": result.errors,
        }

    def batch_delete(self, message_ids: list[str]) -> dict:
        """
        Löscht mehrere E-Mails endgültig (Batch-Operation).
        
        Args:
            message_ids: Liste von Message-IDs.
        
        Returns:
            Statistik-Dictionary mit success/failed/total.
        """
        result = self._batch_processor.delete_messages(message_ids)
        logger.info(f"Batch Delete: {result}")
        return {
            "total": result.total,
            "success": result.success,
            "failed": result.failed,
            "success_rate": result.success_rate,
            "errors": result.errors,
        }

    def batch_trash(self, message_ids: list[str]) -> dict:
        """
        Verschiebt mehrere E-Mails in den Papierkorb.

        Args:
            message_ids: Liste von Message-IDs.

        Returns:
            Statistik-Dictionary mit success/failed/total.
        """
        result = self._batch_processor.trash_messages(message_ids)
        logger.info(f"Batch Trash: {result}")
        return {
            "total": result.total,
            "success": result.success,
            "failed": result.failed,
            "success_rate": result.success_rate,
            "errors": result.errors,
        }

    # ─── Volltextsuche ────────────────────────────────────────────────────────

    def fulltext_search(
        self,
        search_term: str,
        max_results: int = 20,
        label_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Durchsucht E-Mail-Bodies nach einem Suchbegriff.

        Nutzt die Gmail-Vorfilterung und vergleicht anschliessend
        den vollstaendigen Body fuer exakte Treffer.

        Args:
            search_term: Der Suchbegriff (Gross/Kleinschreibung wird ignoriert).
            max_results: Maximale Anzahl der Ergebnisse (1-100).
            label_ids: Optionale Label-Filter.

        Returns:
            Liste mit E-Mail-Details inkl. match_context.
        """
        return self._client.fulltext_search(
            search_term=search_term,
            max_results=max_results,
            label_ids=label_ids,
        )

    def clear_cache(self) -> None:
        """Löscht den Cache (z.B. nach Änderungen an Labels oder Profil)."""
        self._cache.clear()
        logger.info("Cache geleert")

