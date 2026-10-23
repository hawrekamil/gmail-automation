"""
Beispiele für die neuen Verbesserungen:
  - Batch-Operationen für effiziente Verarbeitung mehrerer E-Mails
  - Caching für Labels und Profil
  - Verbessertes Error-Handling
"""

from gmail_bot.services import EmailService
from gmail_bot.core import RateLimitError, MessageNotFoundError
from gmail_bot.utils.logger import get_logger

logger = get_logger(__name__)


def example_batch_operations():
    """
    Beispiel: Batch-Operationen für mehrere E-Mails.
    
    Verwende Batch-Operationen, um mehrere E-Mails gleichzeitig zu verarbeiten.
    Dies ist viel effizienter als Einzeloperationen.
    """
    print("\n" + "=" * 60)
    print("  Batch-Operationen Beispiel")
    print("=" * 60)
    
    service = EmailService()
    
    # Hole 10 ungelesene E-Mails
    unread = service.get_unread(max_results=10)
    message_ids = [email.id for email in unread]
    
    if not message_ids:
        print("Keine ungelesenen E-Mails gefunden.")
        return
    
    print(f"\nFunde {len(message_ids)} ungelesene E-Mails.")
    
    # Batch-Operation: Alle als gelesen markieren
    print("\n1. Markiere alle Mails als gelesen (Batch)...")
    result = service.batch_mark_as_read(message_ids)
    print(f"   ✓ {result['success']}/{result['total']} erfolgreich ({result['success_rate']:.0f}%)")
    
    # Batch-Operation: Label anwenden
    labels = service.get_labels()
    if labels:
        label_id = labels[0]["id"]
        print(f"\n2. Wende Label '{labels[0]['name']}' auf {len(message_ids)} Mails an (Batch)...")
        result = service.batch_apply_label(message_ids, label_id)
        print(f"   ✓ {result['success']}/{result['total']} erfolgreich ({result['success_rate']:.0f}%)")


def example_caching():
    """
    Beispiel: Caching für häufige Abfragen.
    
    Labels und Profil werden automatisch gecacht, um API-Calls zu sparen.
    """
    print("\n" + "=" * 60)
    print("  Caching Beispiel")
    print("=" * 60)
    
    service = EmailService()
    
    # Erste Abfrage – lädt von der API
    print("\n1. Erste Profil-Abfrage (von API)...")
    profile1 = service.get_profile(use_cache=True)
    print(f"   ✓ Eingeloggt als: {profile1['email']}")
    
    # Zweite Abfrage – aus Cache!
    print("\n2. Zweite Profil-Abfrage (aus Cache)...")
    profile2 = service.get_profile(use_cache=True)
    print(f"   ✓ Eingeloggt als: {profile2['email']} [aus Cache]")
    
    # Labels mit Caching
    print("\n3. Labels abrufen (mit Cache)...")
    labels = service.get_labels(use_cache=True)
    print(f"   ✓ {len(labels)} Labels gefunden")
    
    # Cache invalidieren
    print("\n4. Cache leeren...")
    service.clear_cache()
    print("   ✓ Cache geleert")


def example_error_handling():
    """
    Beispiel: Verbessertes Error-Handling mit typsicheren Exceptions.
    
    Verschiedene Fehlertypen können gezielt behandelt werden.
    """
    print("\n" + "=" * 60)
    print("  Error-Handling Beispiel")
    print("=" * 60)
    
    service = EmailService()
    
    # Fehler: Nachricht nicht gefunden
    print("\n1. Versuche nicht-existente E-Mail zu lesen...")
    try:
        service.read_email("INVALID_MESSAGE_ID_12345")
    except MessageNotFoundError as e:
        print(f"   ✗ {e}")
        print(f"     Details: {e.details}")
    
    # Fehler: Validierungs-Fehler
    from gmail_bot.core import ValidationError
    
    print("\n2. Versuche ungültige E-Mail zu senden...")
    try:
        service.send(to="invalid-email", subject="Test", body="Test")
    except ValidationError as e:
        print(f"   ✗ {e}")
        print(f"     Details: {e.details}")
    
    # Rate Limit Fehler (Beispiel)
    print("\n3. Rate Limit Fehler (Simuliert)...")
    try:
        raise RateLimitError(
            "Gmail API Rate-Limit überschritten",
            retry_after=120,
        )
    except RateLimitError as e:
        print(f"   ✗ {e}")
        print(f"     Warte {e.retry_after} Sekunden und versuche erneut")


def example_batch_processor():
    """
    Beispiel: Direkter Zugriff auf BatchProcessor für Custom-Logik.
    """
    print("\n" + "=" * 60)
    print("  Batch-Processor Custom-Logic Beispiel")
    print("=" * 60)
    
    service = EmailService()
    
    # Hole ungelesene E-Mails
    unread = service.get_unread(max_results=5)
    message_ids = [email.id for email in unread]
    
    if not message_ids:
        print("Keine ungelesenen E-Mails gefunden.")
        return
    
    # Verwende BatchProcessor für Custom-Logik
    processor = service.get_batch_processor()
    
    def my_custom_logic(msg_id: str) -> bool:
        """Custom-Logik für jede E-Mail."""
        try:
            email = service.read_email(msg_id)
            # Beispiel: Prüfe ob Betreff spezifisches Wort enthält
            if "wichtig" in email.subject.lower():
                logger.info(f"Wichtige E-Mail gefunden: {email.subject}")
                return True
            return False
        except Exception as e:
            logger.error(f"Fehler: {e}")
            return False
    
    print(f"\nVerarbeite {len(message_ids)} E-Mails mit Custom-Logik...")
    result = processor.process_with_callback(message_ids, my_custom_logic, batch_size=5)
    print(f"✓ {result.success}/{result.total} Mails verarbeitet ({result.success_rate:.0f}%)")


if __name__ == "__main__":
    # Führe Beispiele aus
    # example_batch_operations()
    # example_caching()
    # example_error_handling()
    # example_batch_processor()
    
    print("Uncomment die Funktionen oben, um die Beispiele zu starten!")
