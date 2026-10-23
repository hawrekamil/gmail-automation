"""
Batch-Operationen fuer effiziente Verarbeitung mehrerer E-Mails.

Nutzt die Gmail-Endpunkte batchModify und batchDelete, damit grosse
Aktionen nicht eine API-Anfrage pro E-Mail ausloesen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from gmail_bot.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BatchResult:
    """Ergebnis einer Batch-Operation."""

    total: int
    success: int
    failed: int
    errors: list[dict[str, Any]]

    @property
    def success_rate(self) -> float:
        """Gibt die Erfolgsrate in Prozent zurueck (0-100)."""
        return (self.success / self.total * 100) if self.total > 0 else 0

    def __str__(self) -> str:
        rate = self.success_rate
        return (
            f"Batch-Operation: {self.success}/{self.total} erfolgreich "
            f"({rate:.0f}%) | {self.failed} Fehler"
        )


class BatchProcessor:
    """Verarbeitet E-Mail-Operationen mit echten Gmail-Batch-Endpunkten."""

    def __init__(self, gmail_service: Any):
        self._service = gmail_service
        self._user_id = "me"
        self._chunk_size = 1000

    def _chunks(self, message_ids: list[str]) -> list[list[str]]:
        """Teilt Message-IDs in Gmail-kompatible Bloecke."""
        return [
            message_ids[i:i + self._chunk_size]
            for i in range(0, len(message_ids), self._chunk_size)
        ]

    def mark_as_read(self, message_ids: list[str]) -> BatchResult:
        """Markiert mehrere E-Mails als gelesen."""
        return self._batch_modify_labels(
            message_ids,
            add_labels=[],
            remove_labels=["UNREAD"],
        )

    def mark_as_unread(self, message_ids: list[str]) -> BatchResult:
        """Markiert mehrere E-Mails als ungelesen."""
        return self._batch_modify_labels(
            message_ids,
            add_labels=["UNREAD"],
            remove_labels=[],
        )

    def apply_label(self, message_ids: list[str], label_id: str) -> BatchResult:
        """Wendet ein Label auf mehrere E-Mails an."""
        return self._batch_modify_labels(
            message_ids,
            add_labels=[label_id],
            remove_labels=[],
        )

    def remove_label(self, message_ids: list[str], label_id: str) -> BatchResult:
        """Entfernt ein Label von mehreren E-Mails."""
        return self._batch_modify_labels(
            message_ids,
            add_labels=[],
            remove_labels=[label_id],
        )

    def move_messages(self, message_ids: list[str], add_label_id: str, remove_label_id: str) -> BatchResult:
        """Verschiebt E-Mails in ein neues Label und entfernt das alte."""
        return self._batch_modify_labels(
            message_ids,
            add_labels=[add_label_id],
            remove_labels=[remove_label_id],
        )

    def trash_messages(self, message_ids: list[str]) -> BatchResult:
        """Verschiebt mehrere E-Mails per batchModify in den Papierkorb."""
        return self._batch_modify_labels(
            message_ids,
            add_labels=["TRASH"],
            remove_labels=["INBOX", "SPAM"],
        )

    def delete_messages(self, message_ids: list[str]) -> BatchResult:
        """Loescht mehrere E-Mails endgueltig mit Gmail batchDelete."""
        success, failed, errors = 0, 0, []

        for chunk in self._chunks(message_ids):
            try:
                self._service.users().messages().batchDelete(
                    userId=self._user_id,
                    body={"ids": chunk},
                ).execute()
                success += len(chunk)
                logger.debug(f"{len(chunk)} E-Mail(s) geloescht")
            except Exception as exc:
                failed += len(chunk)
                errors.append({"message_ids": chunk, "error": str(exc)})
                logger.warning(
                    f"Fehler beim Batch-Loeschen von {len(chunk)} E-Mail(s): {exc}"
                )

        result = BatchResult(
            total=len(message_ids),
            success=success,
            failed=failed,
            errors=errors,
        )
        logger.info(f"Batch-Loeschung abgeschlossen: {result}")
        return result

    def process_with_callback(
        self,
        message_ids: list[str],
        callback: Callable[[str], bool],
        batch_size: int = 10,
    ) -> BatchResult:
        """Verarbeitet E-Mails mit einer Callback-Funktion."""
        success, failed, errors = 0, 0, []

        for i, msg_id in enumerate(message_ids):
            try:
                if callback(msg_id):
                    success += 1
                else:
                    failed += 1
                    errors.append({"message_id": msg_id, "error": "Callback returned False"})
            except Exception as exc:
                failed += 1
                errors.append({"message_id": msg_id, "error": str(exc)})
                logger.warning(f"Callback-Fehler fuer {msg_id}: {exc}")

            if (i + 1) % batch_size == 0:
                logger.info(f"Batch-Verarbeitung: {i + 1}/{len(message_ids)} abgeschlossen")

        result = BatchResult(
            total=len(message_ids),
            success=success,
            failed=failed,
            errors=errors,
        )
        logger.info(f"Batch-Callback-Verarbeitung abgeschlossen: {result}")
        return result

    def _batch_modify_labels(
        self,
        message_ids: list[str],
        add_labels: list[str],
        remove_labels: list[str],
    ) -> BatchResult:
        """Fuehrt Label-Aenderungen mit Gmail batchModify in 1000er-Bloecken aus."""
        success, failed, errors = 0, 0, []

        for chunk in self._chunks(message_ids):
            try:
                self._service.users().messages().batchModify(
                    userId=self._user_id,
                    body={
                        "ids": chunk,
                        "addLabelIds": add_labels,
                        "removeLabelIds": remove_labels,
                    },
                ).execute()
                success += len(chunk)
                logger.debug(f"Labels fuer {len(chunk)} E-Mail(s) modifiziert")
            except Exception as exc:
                failed += len(chunk)
                errors.append({"message_ids": chunk, "error": str(exc)})
                logger.warning(
                    f"Fehler beim Batch-Modifizieren von {len(chunk)} E-Mail(s): {exc}"
                )

        result = BatchResult(
            total=len(message_ids),
            success=success,
            failed=failed,
            errors=errors,
        )
        logger.info(f"Batch-Modify abgeschlossen: {result}")
        return result
