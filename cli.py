"""
Gmail Automation CLI – Kommandozeilen-Interface.

Ermöglicht direkte Kommandos ohne Menü:

Verwendung:
    # Labels auflisten
    python cli.py list-labels
    
    # E-Mails in Posteingang anzeigen
    python cli.py list-emails --label INBOX --max 10
    
    # Nach Absender filtern
    python cli.py filter-emails --label INBOX --sender "boss@company.com"
    
    # E-Mails von Absender LÖSCHEN (mit Bestätigung)
    python cli.py delete-emails-by-sender --label INBOX --sender "spam@evil.com" --confirm
    
    # Profil anzeigen
    python cli.py show-profile
    
    # E-Mails als gelesen markieren (Batch)
    python cli.py batch-mark-read --label SNOOZED
"""

import sys
import argparse

from gmail_bot.services import EmailService
from gmail_bot.utils.logger import get_logger

# Windows-Konsole auf UTF-8 umstellen
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logger = get_logger(__name__)


def sender_query(sender_filter: str) -> str:
    """Erstellt eine Gmail-Query fuer Absenderfilter."""
    return f"from:{sender_filter.strip()}"


def print_section(title: str):
    """Gibt einen formatierten Sektions-Header aus."""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70 + "\n")


def cmd_list_labels(args):
    """Listet alle verfügbaren Labels auf."""
    service = EmailService()
    labels = service.get_labels(use_cache=True)
    
    print_section("📂 Verfügbare Labels")
    
    print(f"  {'ID':<20} {'Name':<40}")
    print("  " + "-" * 60)
    
    for label in labels[:20]:  # Begrenze auf 20
        label_id = label.get("id", "")[:18]
        label_name = label.get("name", "")[:38]
        print(f"  {label_id:<20} {label_name:<40}")
    
    if len(labels) > 20:
        print(f"\n  ... und {len(labels) - 20} weitere Labels")
    
    print()


def cmd_show_profile(args):
    """Zeigt das Gmail-Profil an."""
    service = EmailService()
    profile = service.get_profile(use_cache=True)
    
    print_section("📊 Gmail Profil")
    
    print(f"  Email:           {profile.get('email', 'N/A')}")
    print(f"  Nachrichten:     {profile.get('messages_total', 'N/A')}")
    print(f"  Threads:         {profile.get('threads_total', 'N/A')}")
    print()


def cmd_list_emails(args):
    """Listet E-Mails eines Labels auf."""
    service = EmailService()
    
    label_id = args.label or "INBOX"
    max_results = min(args.max, 100)
    
    print_section(f"📧 E-Mails in '{label_id}'")
    
    try:
        emails = service._client.list_messages(
            max_results=max_results,
            label_ids=[label_id]
        )
    except Exception as e:
        print(f"  ❌ Fehler: {e}\n")
        return
    
    if not emails:
        print(f"  ℹ️  Keine E-Mails gefunden.\n")
        return
    
    print(f"  Gefunden: {len(emails)} E-Mail(s)\n")
    
    print(f"  {'#':<3} {'Status':<8} {'Betreff':<35} {'Von':<25}")
    print("  " + "-" * 70)
    
    for i, email in enumerate(emails, 1):
        status = "🔴 NEU" if email.get("is_unread") else "✓"
        subject = email.get("subject", "(kein Betreff)")[:33]
        sender = email.get("from", "")[:23]
        
        print(f"  {i:<3} {status:<8} {subject:<35} {sender:<25}")
    
    print()


def cmd_filter_emails(args):
    """Filtert E-Mails nach Absender."""
    service = EmailService()
    
    label_id = args.label or "INBOX"
    sender_filter = args.sender
    
    if not sender_filter:
        print("  ❌ Bitte --sender angeben\n")
        return
    
    print_section(f"🔍 E-Mails von '{sender_filter}' in '{label_id}'")
    
    try:
        query = sender_query(sender_filter)
        matching_ids = service.get_all_message_ids(label_id, query=query)
        matching = service._client.list_messages(
            max_results=50,
            query=query,
            label_ids=[label_id]
        )
    except Exception as e:
        print(f"  ❌ Fehler: {e}\n")
        return

    if not matching_ids:
        print(f"  ℹ️  Keine E-Mails gefunden.\n")
        return
    
    print(f"  Gefunden: {len(matching_ids)} E-Mail(s)")
    if len(matching_ids) > len(matching):
        print(f"  Zeige die ersten {len(matching)} Treffer.\n")
    else:
        print()
    
    for i, email in enumerate(matching, 1):
        status = "🔴 NEU" if email.get("is_unread") else "✓"
        subject = email.get("subject", "(kein Betreff)")
        sender = email.get("from", "")
        date = email.get("date", "")
        
        print(f"  [{status}] {subject}")
        print(f"       Von:   {sender}")
        print(f"       Datum: {date}")
        print()


def cmd_batch_mark_read(args):
    """Markiert E-Mails eines Labels als gelesen (Batch)."""
    service = EmailService()
    
    label_id = args.label or "INBOX"
    
    print_section(f"📧 Markiere E-Mails in '{label_id}' als gelesen")
    
    try:
        # Hole E-Mails
        msg_ids = service.get_all_message_ids(label_id)
        
        if not msg_ids:
            print(f"  ℹ️  Keine E-Mails gefunden.\n")
            return
        
        # Batch-Operation
        result = service.batch_mark_as_read(msg_ids)
        
        print(f"  ✅ Erfolg:      {result['success']} E-Mail(s)")
        print(f"  ❌ Fehler:      {result['failed']} E-Mail(s)")
        print(f"  📊 Rate:        {result['success_rate']:.0f}%")
        print()
    
    except Exception as e:
        print(f"  ❌ Fehler: {e}\n")


def cmd_batch_apply_label(args):
    """Wendet ein Label auf E-Mails eines anderen Labels an."""
    service = EmailService()
    
    source_label = args.source or "INBOX"
    target_label = args.target
    
    if not target_label:
        print("  ❌ Bitte --target angeben\n")
        return
    
    print_section(f"🏷️  Wende Label '{target_label}' auf E-Mails an")
    
    try:
        # Hole Labels
        labels = service.get_labels()
        target_id = next(
            (l["id"] for l in labels if l["name"] == target_label),
            None
        )
        
        if not target_id:
            print(f"  ❌ Label '{target_label}' nicht gefunden\n")
            return
        
        # Hole E-Mails
        msg_ids = service.get_all_message_ids(source_label)
        
        if not msg_ids:
            print(f"  ℹ️  Keine E-Mails gefunden.\n")
            return
        
        # Batch-Operation
        result = service.batch_apply_label(msg_ids, target_id)
        
        print(f"  ✅ Erfolg:      {result['success']} E-Mail(s)")
        print(f"  ❌ Fehler:      {result['failed']} E-Mail(s)")
        print(f"  📊 Rate:        {result['success_rate']:.0f}%")
        print()
    
    except Exception as e:
        print(f"  ❌ Fehler: {e}\n")


def cmd_delete_emails_by_sender(args):
    """Löscht alle E-Mails von einem bestimmten Absender (mit Bestätigung)."""
    service = EmailService()
    
    label_id = args.label or "INBOX"
    sender_filter = args.sender
    
    if not sender_filter:
        print("  ❌ Bitte --sender angeben\n")
        return
    
    print_section(f"🗑️  Löschen von E-Mails aus '{label_id}'")
    
    try:
        query = sender_query(sender_filter)
        msg_ids = service.get_all_message_ids(label_id, query=query)
        matching = service._client.list_messages(
            max_results=5,
            query=query,
            label_ids=[label_id]
        )
        
        if not msg_ids:
            print(f"  ℹ️  Keine E-Mails von '{sender_filter}' gefunden.\n")
            return
        
        print(f"  🔍 Gefunden: {len(msg_ids)} E-Mail(s) von '{sender_filter}'")
        print()
        
        # Zeige Vorschau
        print("  Vorschau (erste 5):")
        for i, email in enumerate(matching, 1):
            subject = email.get("subject", "(kein Betreff)")[:50]
            date = email.get("date", "")
            print(f"    {i}. {subject}")
            print(f"       {date}")
        
        if len(msg_ids) > 5:
            print(f"    ... und {len(msg_ids) - 5} weitere")
        
        print()
        
        # Sicherheitsabfrage
        if not args.confirm:
            response = input(
                f"  ⚠️  Wirklich {len(msg_ids)} E-Mail(s) löschen? "
                f"(ja/nein): "
            ).strip().lower()
            
            if response not in ("ja", "yes", "y"):
                print("  ❌ Abgebrochen.\n")
                return
        else:
            print("  ⚠️  --confirm Flag gesetzt, lösche ohne Bestätigung...\n")
        
        # Lösche E-Mails
        result = service.batch_delete(msg_ids)
        
        print(f"\n  ✅ Erfolg:      {result['success']} E-Mail(s) gelöscht")
        print(f"  ❌ Fehler:      {result['failed']} E-Mail(s)")
        print(f"  📊 Rate:        {result['success_rate']:.0f}%")
        print()
    
    except Exception as e:
        print(f"  ❌ Fehler: {e}\n")


def cmd_trash_emails_by_sender(args):
    """Verschiebt alle E-Mails von einem bestimmten Absender in den Papierkorb."""
    service = EmailService()

    label_id = args.label or "INBOX"
    sender_filter = args.sender

    if not sender_filter:
        print("  ❌ Bitte --sender angeben\n")
        return

    print_section(f"🗑️  Papierkorb für E-Mails aus '{label_id}'")

    try:
        query = sender_query(sender_filter)
        msg_ids = service.get_all_message_ids(label_id, query=query)
        matching = service._client.list_messages(
            max_results=5,
            query=query,
            label_ids=[label_id]
        )

        if not msg_ids:
            print(f"  ℹ️  Keine E-Mails von '{sender_filter}' gefunden.\n")
            return

        print(f"  🔍 Gefunden: {len(msg_ids)} E-Mail(s) von '{sender_filter}'")
        print()

        print("  Vorschau (erste 5):")
        for i, email in enumerate(matching, 1):
            subject = email.get("subject", "(kein Betreff)")[:50]
            date = email.get("date", "")
            print(f"    {i}. {subject}")
            print(f"       {date}")

        if len(msg_ids) > 5:
            print(f"    ... und {len(msg_ids) - 5} weitere")

        print()

        if not args.confirm:
            response = input(
                f"  ⚠️  Wirklich {len(msg_ids)} E-Mail(s) in den Papierkorb verschieben? "
                f"(ja/nein): "
            ).strip().lower()

            if response not in ("ja", "yes", "y"):
                print("  ❌ Abgebrochen.\n")
                return
        else:
            print("  ⚠️  --confirm Flag gesetzt, verschiebe ohne Bestätigung...\n")

        result = service.batch_trash(msg_ids)

        print(f"\n  ✅ Erfolg:      {result['success']} E-Mail(s) in Papierkorb")
        print(f"  ❌ Fehler:      {result['failed']} E-Mail(s)")
        print(f"  📊 Rate:        {result['success_rate']:.0f}%")
        print()

    except Exception as e:
        print(f"  ❌ Fehler: {e}\n")


def cmd_delete_all_in_label(args):
    """Löscht ALLE E-Mails in einem Label (mit Bestätigung)."""
    service = EmailService()
    
    label_id = args.label or "INBOX"
    
    print_section(f"🗑️  Löschen aller E-Mails aus '{label_id}'")
    
    try:
        # Hole alle E-Mails des Labels
        msg_ids = service.get_all_message_ids(label_id)
        preview_emails = service._client.list_messages(
            max_results=5,
            label_ids=[label_id]
        )
        
        if not msg_ids:
            print(f"  ℹ️  Keine E-Mails in '{label_id}' gefunden.\n")
            return
        
        total_count = len(msg_ids)
        print(f"  🔍 Gefunden: {total_count} E-Mail(s) in '{label_id}'")
        print()
        
        # Zeige Vorschau
        print("  Vorschau (erste 5):")
        for i, email in enumerate(preview_emails, 1):
            subject = email.get("subject", "(kein Betreff)")[:50]
            date = email.get("date", "")
            print(f"    {i}. {subject}")
            print(f"       {date}")
        
        if total_count > 5:
            print(f"    ... und {total_count - 5} weitere")
        
        print()
        
        # Sicherheitsabfrage (doppelt!)
        if not args.confirm:
            response1 = input(
                f"  ⚠️  Wirklich {total_count} E-Mail(s) löschen? (ja/nein): "
            ).strip().lower()
            
            if response1 not in ("ja", "yes", "y"):
                print("  ❌ Abgebrochen.\n")
                return
            
            # Doppelt-Bestätigung für große Mengen
            if total_count > 50:
                response2 = input(
                    f"  🚨 ENDGÜLTIG {total_count} E-MAILS LÖSCHEN? Nicht rückgängig machbar! (ja/nein): "
                ).strip().lower()
                
                if response2 not in ("ja", "yes", "y"):
                    print("  ❌ Abgebrochen.\n")
                    return
        else:
            print(f"  ⚠️  --confirm Flag gesetzt, lösche {total_count} E-Mail(s) ohne Bestätigung...\n")
        
        # Lösche E-Mails
        result = service.batch_delete(msg_ids)
        
        print(f"\n  ✅ Erfolg:      {result['success']} E-Mail(s) gelöscht")
        print(f"  ❌ Fehler:      {result['failed']} E-Mail(s)")
        print(f"  📊 Rate:        {result['success_rate']:.0f}%")
        print()
    
    except Exception as e:
        print(f"  ❌ Fehler: {e}\n")


def cmd_trash_all_in_label(args):
    """Verschiebt ALLE E-Mails in einem Label in den Papierkorb (sicherer)."""
    service = EmailService()
    
    label_id = args.label or "INBOX"
    
    print_section(f"🗑️  Verschiebe alle E-Mails aus '{label_id}' in Papierkorb")
    
    try:
        # Hole alle E-Mails
        msg_ids = service.get_all_message_ids(label_id)
        
        if not msg_ids:
            print(f"  ℹ️  Keine E-Mails in '{label_id}' gefunden.\n")
            return
        
        total_count = len(msg_ids)
        print(f"  🔍 Gefunden: {total_count} E-Mail(s)")
        print()
        
        # Sicherheitsabfrage
        if not args.confirm:
            response = input(
                f"  ⚠️  {total_count} E-Mail(s) in Papierkorb verschieben? (ja/nein): "
            ).strip().lower()
            
            if response not in ("ja", "yes", "y"):
                print("  ❌ Abgebrochen.\n")
                return
        
        # Verschiebe E-Mails
        result = service.batch_trash(msg_ids)
        
        print(f"\n  ✅ Erfolg:      {result['success']} E-Mail(s) in Papierkorb")
        print(f"  ❌ Fehler:      {result['failed']} E-Mail(s)")
        print(f"  📊 Rate:        {result['success_rate']:.0f}%")
        print()
    
    except Exception as e:
        print(f"  ❌ Fehler: {e}\n")




def main():
    """Hauptfunktion für CLI."""
    parser = argparse.ArgumentParser(
        description="Gmail Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python cli.py list-labels
  python cli.py list-emails --label INBOX --max 10
  python cli.py filter-emails --label INBOX --sender "boss@company.com"
  python cli.py show-profile
  python cli.py batch-mark-read --label SNOOZED
  python cli.py batch-apply-label --source INBOX --target MyLabel
  python cli.py trash-all-in-label --label SPAM
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Befehl")
    
    # list-labels
    subparsers.add_parser("list-labels", help="Alle Labels auflisten")
    
    # show-profile
    subparsers.add_parser("show-profile", help="Gmail-Profil anzeigen")
    
    # list-emails
    parser_list = subparsers.add_parser(
        "list-emails",
        help="E-Mails in einem Label auflisten"
    )
    parser_list.add_argument(
        "--label",
        default="INBOX",
        help="Label-ID (default: INBOX)"
    )
    parser_list.add_argument(
        "--max",
        type=int,
        default=10,
        help="Maximale Anzahl (default: 10, max: 100)"
    )
    
    # filter-emails
    parser_filter = subparsers.add_parser(
        "filter-emails",
        help="E-Mails nach Absender filtern"
    )
    parser_filter.add_argument(
        "--label",
        default="INBOX",
        help="Label-ID (default: INBOX)"
    )
    parser_filter.add_argument(
        "--sender",
        required=True,
        help="Absender (Name oder Email)"
    )
    
    # batch-mark-read
    parser_mark = subparsers.add_parser(
        "batch-mark-read",
        help="Alle E-Mails eines Labels als gelesen markieren"
    )
    parser_mark.add_argument(
        "--label",
        default="INBOX",
        help="Label-ID (default: INBOX)"
    )
    
    # batch-apply-label
    parser_apply = subparsers.add_parser(
        "batch-apply-label",
        help="Label auf E-Mails anwenden"
    )
    parser_apply.add_argument(
        "--source",
        default="INBOX",
        help="Quell-Label (default: INBOX)"
    )
    parser_apply.add_argument(
        "--target",
        required=True,
        help="Ziel-Label"
    )
    
    # delete-emails-by-sender
    parser_delete = subparsers.add_parser(
        "delete-emails-by-sender",
        help="Löscht alle E-Mails von einem Absender (ENDGÜLTIG!)"
    )
    parser_delete.add_argument(
        "--label",
        default="INBOX",
        help="Label-ID (default: INBOX)"
    )
    parser_delete.add_argument(
        "--sender",
        required=True,
        help="Absender (Name oder Email)"
    )
    parser_delete.add_argument(
        "--confirm",
        action="store_true",
        help="Überspringe die Bestätigungsfrage (Vorsicht!)"
    )
    
    # trash-emails-by-sender
    parser_trash = subparsers.add_parser(
        "trash-emails-by-sender",
        help="Verschiebt E-Mails von Absender in Papierkorb (sicherer)"
    )
    parser_trash.add_argument(
        "--label",
        default="INBOX",
        help="Label-ID (default: INBOX)"
    )
    parser_trash.add_argument(
        "--sender",
        required=True,
        help="Absender (Name oder Email)"
    )
    parser_trash.add_argument(
        "--confirm",
        action="store_true",
        help="Überspringe die Bestätigungsfrage"
    )

    # delete-all-in-label
    parser_delete_all = subparsers.add_parser(
        "delete-all-in-label",
        help="Löscht alle E-Mails in einem Label endgültig"
    )
    parser_delete_all.add_argument(
        "--label",
        default="INBOX",
        help="Label-ID (default: INBOX)"
    )
    parser_delete_all.add_argument(
        "--confirm",
        action="store_true",
        help="Überspringe die Bestätigungsfrage (Vorsicht!)"
    )

    # trash-all-in-label
    parser_trash_all = subparsers.add_parser(
        "trash-all-in-label",
        help="Verschiebt alle E-Mails in einem Label in den Papierkorb"
    )
    parser_trash_all.add_argument(
        "--label",
        default="INBOX",
        help="Label-ID (default: INBOX)"
    )
    parser_trash_all.add_argument(
        "--confirm",
        action="store_true",
        help="Überspringe die Bestätigungsfrage"
    )
    
    args = parser.parse_args()
    
    # Kommandos ausführen
    commands = {
        "list-labels": cmd_list_labels,
        "show-profile": cmd_show_profile,
        "list-emails": cmd_list_emails,
        "filter-emails": cmd_filter_emails,
        "batch-mark-read": cmd_batch_mark_read,
        "batch-apply-label": cmd_batch_apply_label,
        "delete-emails-by-sender": cmd_delete_emails_by_sender,
        "trash-emails-by-sender": cmd_trash_emails_by_sender,
        "delete-all-in-label": cmd_delete_all_in_label,
        "trash-all-in-label": cmd_trash_all_in_label,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
