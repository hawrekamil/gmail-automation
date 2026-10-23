"""
Gmail Automation – Interaktives Einstiegspunkt.

Startet den Gmail Bot mit Menü-System zur Navigation:
  - Verfügbare Labels/Ordner anzeigen
  - E-Mails in einem Ordner auflisten
  - Nach Absender (Name/Email) filtern
  - Profil anzeigen

Verwendung:
    python main.py
"""

import sys

from gmail_bot.services import EmailService
from gmail_bot.utils.logger import get_logger

# Windows-Konsole auf UTF-8 umstellen (für Emojis in E-Mail-Betreffs)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logger = get_logger(__name__)

# ─── Vordefinierte Label-Namen für schnelle Auswahl ─────────────────────────

COMMON_LABELS = {
    "1": ("INBOX", "📥 Posteingang"),
    "2": ("SNOOZED", "⏰ Snooze"),
    "3": ("SOCIAL", "👥 Sozial"),
    "4": ("UPDATES", "🔔 Updates"),
    "5": ("PROMOTIONS", "🎉 Promotions"),
    "6": ("SPAM", "🚫 Spam"),
}


def print_header(title: str):
    """Gibt einen formatierten Header aus."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """Gibt einen formatierten Sektions-Header aus."""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70)


def print_batch_result(result: dict, success_text: str, failure_text: str):
    """Gibt Batch-Ergebnisse ohne falsche Erfolgsmeldung aus."""
    if result["success"] == result["total"]:
        print(f"\n  ✅ {result['success']}/{result['total']} {success_text}\n")
    elif result["success"] > 0:
        print(f"\n  ⚠️  {result['success']}/{result['total']} {success_text}")
        print(f"     {result['failed']} fehlgeschlagen.\n")
    else:
        print(f"\n  ❌ 0/{result['total']} {failure_text}")
        if result.get("errors"):
            print(f"     Erster Fehler: {result['errors'][0].get('error', 'Unbekannt')[:180]}")
        print()


def show_profile(service: EmailService):
    """Zeigt das Gmail-Profil an."""
    print_header("📊 Gmail Profil")
    
    profile = service.get_profile(use_cache=True)
    print(f"\n  Email:          {profile['email']}")
    print(f"  Nachrichten:    {profile['messages_total']}")
    print(f"  Threads:        {profile['threads_total']}")
    print()


def show_labels(service: EmailService) -> dict[str, tuple[str, str]]:
    """Zeigt alle verfügbaren Labels/Ordner an."""
    print_header("📂 Verfügbare Labels/Ordner")
    
    labels = service.get_labels(use_cache=False)
    
    # Gruppe 1: Vordefinierte Labels
    print("\n  🌟 Häufig verwendete Labels:")
    for key, (label_id, display_name) in COMMON_LABELS.items():
        # Prüfe ob dieses Label existiert
        label_exists = any(l["id"] == label_id for l in labels)
        if label_exists:
            print(f"    [{key}] {display_name}")
    
    # Gruppe 2: Benutzerdefinierte Labels
    custom_labels = [l for l in labels if l["id"] not in [v[0] for v in COMMON_LABELS.values()]]
    if custom_labels:
        print("\n  ✨ Benutzerdefinierte Labels:")
        for i, label in enumerate(custom_labels, 7):
            print(f"    [{i}] {label['name']}")
    
    print()
    return labels


def show_label_emails(service: EmailService, label_id: str, label_name: str):
    """Zeigt E-Mails eines bestimmten Labels an."""
    print_header(f"📧 E-Mails in '{label_name}'")
    
    # Hole E-Mails aus dem Label
    emails = service.search_emails(label_ids=[label_id], max_results=20)
    
    if not emails:
        print("\n  ℹ️  Keine E-Mails gefunden.\n")
        return
    
    print(f"\n  Insgesamt: {len(emails)} E-Mails\n")
    
    for i, email in enumerate(emails, 1):
        status = "[🔴 NEU]" if email.is_unread else "[   ]"
        subject = email.subject[:50]
        sender = email.sender[:40]
        date = email.date
        
        print(f"  {status} {i:2}. {subject}")
        print(f"       Von:   {sender}")
        print(f"       Datum: {date}")
        print()


def confirm_action(prompt: str, danger: bool = False) -> bool:
    """Fragt eine Aktion bestaetigt ab."""
    if danger:
        print("     Diese Aktion kann NICHT rueckgaengig gemacht werden!")
    confirm = input(prompt).strip().lower()
    return confirm in ("ja", "yes", "y")


def sender_query(sender_filter: str) -> str:
    """Erstellt eine Gmail-Query fuer Absenderfilter. Unterstuetzt mehrere Absender getrennt durch Komma."""
    senders = [s.strip() for s in sender_filter.split(",") if s.strip()]
    if not senders:
        return ""
    queries = [f"from:{s}" for s in senders]
    return " OR ".join(queries)


def run_batch_action(service: EmailService, message_ids: list[str], action: str):
    """Fuehrt Papierkorb/Loeschen fuer eine Liste von E-Mails aus."""
    if not message_ids:
        print("\n  ℹ️  Keine E-Mails fuer diese Aktion gefunden.\n")
        return

    if action == "trash":
        print(f"\n  ⚠️  Verschiebe {len(message_ids)} E-Mail(s) in den Papierkorb...")
        if confirm_action("  Bestaetigung (ja/nein): "):
            result = service.batch_trash(message_ids)
            print_batch_result(result, "in den Papierkorb verschoben", "in den Papierkorb verschoben")
        else:
            print("  ❌ Abgebrochen\n")

    elif action == "delete":
        print(f"\n  🚨 ENDGUELTIGES LOESCHEN von {len(message_ids)} E-Mail(s)")
        if confirm_action("  Bist du sicher? (ja/nein): ", danger=True):
            result = service.batch_delete(message_ids)
            print_batch_result(result, "endgueltig geloescht", "endgueltig geloescht")
        else:
            print("  ❌ Abgebrochen\n")


def folder_actions(service: EmailService, label_id: str, label_name: str):
    """Bietet Aktionen fuer alle E-Mails oder einen bestimmten Absender im Ordner."""
    while True:
        print_section(f"Aktionen fuer '{label_name}'")
        print("\n  [1] Alle E-Mails in Papierkorb verschieben")
        print("  [2] Alle E-Mails endgueltig loeschen")
        print("  [3] E-Mails von bestimmtem Absender in Papierkorb verschieben")
        print("  [4] E-Mails von bestimmtem Absender endgueltig loeschen")
        print("  [0] Zurueck")

        choice = input("\n  Wahl eingeben: ").strip()

        if choice == "0":
            return

        if choice in ("1", "2"):
            msg_ids = service.get_all_message_ids(label_id)
            run_batch_action(service, msg_ids, "trash" if choice == "1" else "delete")
            return

        if choice in ("3", "4"):
            sender_filter = input("\n  Absender (Name oder Email) eingeben: ").strip()
            if not sender_filter:
                print("  ⚠️  Keine Eingabe. Abgebrochen.\n")
                return

            query = sender_query(sender_filter)
            msg_ids = service.get_all_message_ids(label_id, query=query)

            if not msg_ids:
                print(f"\n  ℹ️  Keine E-Mails von '{sender_filter}' gefunden.\n")
                return

            preview_emails = service.get_email_previews(
                max_results=5,
                query=query,
                label_ids=[label_id],
            )

            print(f"\n  Gefunden: {len(msg_ids)} E-Mail(s) von '{sender_filter}'")
            for i, email in enumerate(preview_emails, 1):
                subject = email.subject[:55]
                date = email.date
                print(f"    {i}. {subject}")
                print(f"       {date}")
            if len(msg_ids) > 5:
                print(f"    ... und {len(msg_ids) - 5} weitere")

            run_batch_action(service, msg_ids, "trash" if choice == "3" else "delete")
            return

        print(f"  ⚠️  Ungueltige Wahl: '{choice}'\n")


def delete_all_emails_in_folder(service: EmailService):
    """Loescht alle E-Mails in einem ausgewaehlten Ordner endgueltig."""
    labels = service.get_labels(use_cache=False)
    result = menu_select_label(labels)
    if not result:
        return

    label_id, label_name = result
    print_header(f"Alle E-Mails in '{label_name}' endgueltig loeschen")

    print("\n  Lade alle E-Mail-IDs im Ordner...")
    msg_ids = service.get_all_message_ids(label_id)
    if not msg_ids:
        print("\n  ℹ️  Keine E-Mails gefunden.\n")
        return

    preview_emails = service.get_email_previews(max_results=5, label_ids=[label_id])

    print(f"\n  Gefunden: {len(msg_ids)} E-Mail(s)")
    print("\n  Vorschau (erste 5):")
    for i, email in enumerate(preview_emails, 1):
        subject = email.subject[:55]
        sender = email.sender[:45]
        print(f"    {i}. {subject}")
        print(f"       Von: {sender}")
    if len(msg_ids) > 5:
        print(f"    ... und {len(msg_ids) - 5} weitere")

    run_batch_action(service, msg_ids, "delete")


def filter_emails_by_sender(service: EmailService, label_id: str, label_name: str):
    """Filtert E-Mails nach Absender."""
    print_section(f"🔍 Filter E-Mails nach Absender in '{label_name}'")
    
    sender_filter = input("\n  Absender (Name oder Email) eingeben (kommagetrennt für mehrere): ").strip()
    
    if not sender_filter:
        print("  ⚠️  Keine Eingabe. Abgebrochen.\n")
        return
    
    query = sender_query(sender_filter)
    matching_ids = service.get_all_message_ids(label_id, query=query)
    matching_emails = service.search_emails(
        max_results=100,
        query=query,
        label_ids=[label_id],
    )
    
    if not matching_ids:
        print(f"\n  ℹ️  Keine E-Mails von '{sender_filter}' gefunden.\n")
        return
    
    print(f"\n  📍 {len(matching_ids)} E-Mail(s) gefunden")
    if len(matching_ids) > len(matching_emails):
        print(f"     Zeige die ersten {len(matching_emails)} Treffer.\n")
    else:
        print()
    
    for i, email in enumerate(matching_emails, 1):
        status = "[🔴 NEU]" if email.is_unread else "[   ]"
        subject = email.subject
        sender = email.sender
        date = email.date
        
        print(f"  {status} {i}. {subject}")
        print(f"      Von:   {sender}")
        print(f"      Datum: {date}")
        print()
    
    # Frage nach Aktion
    print("-" * 70)
    action = input("\n  Was möchtest du tun?\n  [1] Alle als gelesen markieren\n  [2] Label anwenden (Kopieren)\n  [3] In anderen Ordner/Label umziehen (Verschieben)\n  [4] In Papierkorb verschieben\n  [5] Endgültig löschen\n  [0] Abbrechen\n\n  Wahl: ").strip()
    
    if action == "1":
        result = service.batch_mark_as_read(matching_ids)
        print_batch_result(result, "als gelesen markiert", "als gelesen markiert")
    
    elif action == "2":
        labels = service.get_labels(use_cache=True)
        custom_labels = [l for l in labels if l["id"] not in [v[0] for v in COMMON_LABELS.values()]]
        
        if custom_labels:
            print("\n  Verfügbare Labels:")
            for i, lbl in enumerate(custom_labels, 1):
                print(f"    [{i}] {lbl['name']}")
            
            choice = input("\n  Label-Nummer eingeben: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(custom_labels):
                    target_label_id = custom_labels[idx]["id"]
                    result = service.batch_apply_label(matching_ids, target_label_id)
                    print_batch_result(result, "mit Label versehen", "mit Label versehen")
            except (ValueError, IndexError):
                print("  ⚠️  Ungültige Wahl\n")
        else:
            print("  ⚠️  Keine benutzerdefinierten Labels vorhanden\n")
            
    elif action == "3":
        labels = service.get_labels(use_cache=False)
        custom_labels = [l for l in labels if l["id"] not in [v[0] for v in COMMON_LABELS.values()]]
        
        print("\n  Verfügbare Labels für den Umzug:")
        for i, lbl in enumerate(custom_labels, 1):
            print(f"    [{i}] {lbl['name']}")
        print("    [n] Neues Label erstellen")
        
        choice = input("\n  Label-Nummer oder 'n' eingeben: ").strip().lower()
        if choice == 'n':
            new_label_name = input("  Name des neuen Labels (z.B. Job_angebot): ").strip()
            if new_label_name:
                try:
                    new_label = service.create_label(new_label_name)
                    target_label_id = new_label["id"]
                    result = service.batch_move_to_label(matching_ids, target_label_id, remove_label_id=label_id)
                    print_batch_result(result, f"in neues Label '{new_label_name}' verschoben", f"in neues Label '{new_label_name}' verschoben")
                except Exception as e:
                    print(f"  ❌ Fehler beim Erstellen des Labels: {e}\n")
            else:
                print("  ⚠️  Kein Name eingegeben.\n")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(custom_labels):
                    target_label_id = custom_labels[idx]["id"]
                    result = service.batch_move_to_label(matching_ids, target_label_id, remove_label_id=label_id)
                    print_batch_result(result, "in Ordner verschoben", "in Ordner verschoben")
            except (ValueError, IndexError):
                print("  ⚠️  Ungültige Wahl\n")
    
    elif action == "4":
        print(f"\n  ⚠️  Verschiebe {len(matching_emails)} E-Mail(s) in Papierkorb...")
        confirm = input("  Bestätigung (ja/nein): ").strip().lower()
        
        if confirm in ("ja", "yes", "y"):
            result = service.batch_trash(matching_ids)
            print_batch_result(result, "in den Papierkorb verschoben", "in den Papierkorb verschoben")
        else:
            print("  ❌ Abgebrochen\n")
    
    elif action == "5":
        print(f"\n  🚨 ENDGÜLTIGES LÖSCHEN von {len(matching_emails)} E-Mail(s)")
        print("     Diese Aktion kann NICHT rückgängig gemacht werden!")
        confirm = input("  Bist du sicher? (ja/nein): ").strip().lower()
        
        if confirm in ("ja", "yes", "y"):
            result = service.batch_delete(matching_ids)
            print_batch_result(result, "endgültig gelöscht", "endgültig gelöscht")
        else:
            print("  ❌ Abgebrochen\n")
    
    else:
        print("  ❌ Abgebrochen\n")


def menu_select_label(labels: list[dict[str, str]]) -> tuple[str, str] | None:
    """Zeigt Menü zur Label-Auswahl."""
    print_section("🎯 Label wählen")
    
    print("\n  Vordefinierte Labels:")
    for key, (label_id, display_name) in COMMON_LABELS.items():
        label_exists = any(l["id"] == label_id for l in labels)
        if label_exists:
            print(f"    [{key}] {display_name}")
    
    custom_labels = [l for l in labels if l["id"] not in [v[0] for v in COMMON_LABELS.values()]]
    if custom_labels:
        print("\n  Benutzerdefinierte Labels:")
        for i, label in enumerate(custom_labels, 7):
            print(f"    [{i}] {label['name']}")
    
    choice = input("\n  Wahl eingeben (z.B. '1' für Posteingang) oder 'b' für zurück: ").strip().lower()
    
    if choice == "b":
        return None
    
    # Versuche vordefinierte Label
    if choice in COMMON_LABELS:
        label_id = COMMON_LABELS[choice][0]
        label_name = COMMON_LABELS[choice][1]
        label_exists = any(l["id"] == label_id for l in labels)
        if label_exists:
            return (label_id, label_name)
        else:
            print(f"  ⚠️  Label nicht vorhanden.\n")
            return None
    
    # Versuche benutzerdefiniertes Label
    try:
        idx = int(choice) - 7
        if 0 <= idx < len(custom_labels):
            return (custom_labels[idx]["id"], custom_labels[idx]["name"])
    except (ValueError, IndexError):
        pass
    
    print(f"  ⚠️  Ungültige Wahl: '{choice}'\n")
    return None


def show_all_senders(service: EmailService, labels: list[dict[str, str]]):
    """Listet alle einzigartigen Absender in einem Ordner auf, sortiert nach Häufigkeit."""
    result = menu_select_label(labels)
    if not result:
        return

    label_id, label_name = result
    print_header(f"📋 Alle Absender in '{label_name}'")

    print("  ⏳ Lade E-Mails... (das kann bei vielen E-Mails etwas dauern)\n")

    # Lade alle E-Mails (bis zu 500 Stück für eine gute Übersicht)
    emails = service.search_emails(label_ids=[label_id], max_results=500)

    if not emails:
        print("  ℹ️  Keine E-Mails gefunden.\n")
        return

    # Absender zählen
    from collections import Counter
    sender_counter = Counter()
    for email in emails:
        sender = email.sender.strip()
        if sender:
            sender_counter[sender] += 1

    if not sender_counter:
        print("  ℹ️  Keine Absender gefunden.\n")
        return

    # Nach Häufigkeit sortiert ausgeben
    sorted_senders = sender_counter.most_common()
    total_emails = sum(sender_counter.values())
    unique_count = len(sorted_senders)

    print(f"  📊 {unique_count} verschiedene Absender in {total_emails} E-Mails\n")
    print(f"  {'#':<4} {'Anzahl':<8} {'Absender'}")
    print("  " + "-" * 66)

    for i, (sender, count) in enumerate(sorted_senders, 1):
        # Sender kürzen falls zu lang
        display_sender = sender[:60] if len(sender) > 60 else sender
        print(f"  {i:<4} {count:<8} {display_sender}")

    print(f"\n  {'':>4} {'─'*6}")
    print(f"  {'':>4} {total_emails:<8} Gesamt\n")

    # Optional: Aktion auf einen Absender
    action = input("  Möchtest du E-Mails eines Absenders filtern? (Nummer eingeben oder Enter zum Überspringen): ").strip()
    if action:
        try:
            idx = int(action) - 1
            if 0 <= idx < len(sorted_senders):
                selected_sender = sorted_senders[idx][0]
                # E-Mail-Adresse aus dem Sender-String extrahieren
                if "<" in selected_sender and ">" in selected_sender:
                    email_addr = selected_sender.split("<")[1].split(">")[0]
                else:
                    email_addr = selected_sender
                filter_emails_by_sender(service, label_id, label_name)
            else:
                print("  ⚠️  Ungültige Nummer\n")
        except ValueError:
            print("  ⚠️  Ungültige Eingabe\n")


def fulltext_search_menu(service: EmailService):
    """Volltextsuche in E-Mail-Bodies."""
    print_header("🔍 Volltextsuche in E-Mails")

    search_term = input("\n  Suchbegriff eingeben: ").strip()
    if not search_term:
        print("  ⚠️  Kein Suchbegriff eingegeben.\n")
        return

    # Optional: In bestimmtem Ordner suchen
    print("\n  Wo soll gesucht werden?")
    print("    [1] Überall (alle E-Mails)")
    print("    [2] Nur im Posteingang")
    print("    [3] In einem bestimmten Ordner")
    scope_choice = input("\n  Wahl (Enter für überall): ").strip()

    label_ids = None
    scope_name = "allen E-Mails"
    if scope_choice == "2":
        label_ids = ["INBOX"]
        scope_name = "Posteingang"
    elif scope_choice == "3":
        labels = service.get_labels(use_cache=True)
        result = menu_select_label(labels)
        if result:
            label_ids = [result[0]]
            scope_name = result[1]
        else:
            return

    # Anzahl Ergebnisse
    count_input = input("  Max. Ergebnisse (Enter für 20): ").strip()
    max_results = 20
    if count_input:
        try:
            max_results = max(1, min(int(count_input), 100))
        except ValueError:
            pass

    print(f"\n  ⏳ Durchsuche {scope_name} nach '{search_term}'...")
    print("     (Bodies werden geladen – das kann etwas dauern)\n")

    matches = service.fulltext_search(
        search_term=search_term,
        max_results=max_results,
        label_ids=label_ids,
    )

    if not matches:
        print(f"  ℹ️  Keine Treffer für '{search_term}' gefunden.\n")
        return

    print_section(f"📋 {len(matches)} Treffer für '{search_term}'")

    for i, email in enumerate(matches, 1):
        is_unread = email.get("is_unread", False)
        status = "[🔴 NEU]" if is_unread else "[   ]"
        subject = email.get("subject", "(kein Betreff)")[:60]
        sender = email.get("from", "")[:45]
        date = email.get("date", "")
        context = email.get("match_context", "")

        print(f"  {status} {i:2}. {subject}")
        print(f"       Von:   {sender}")
        print(f"       Datum: {date}")
        if context:
            # Suchbegriff im Kontext hervorheben mit Klammern
            print(f"       💬 ...{context[:120]}")
        print()

    # Aktion auf einen Treffer
    detail_choice = input("  E-Mail-Nummer eingeben für Volltext (oder Enter zum Überspringen): ").strip()
    if detail_choice:
        try:
            idx = int(detail_choice) - 1
            if 0 <= idx < len(matches):
                email = matches[idx]
                print_header(f"📧 {email['subject'][:60]}")
                print(f"\n  Von:    {email.get('from', '')}")
                print(f"  An:     {email.get('to', '')}")
                print(f"  Datum:  {email.get('date', '')}")
                print(f"\n{'-' * 70}")
                # Body anzeigen (begrenzt auf 2000 Zeichen)
                body = email.get("body", "(kein Inhalt)")
                if len(body) > 2000:
                    print(f"  {body[:2000]}")
                    print(f"\n  [...{len(body) - 2000} weitere Zeichen abgeschnitten...]")
                else:
                    print(f"  {body}")
                print(f"{'-' * 70}\n")
            else:
                print("  ⚠️  Ungültige Nummer\n")
        except ValueError:
            print("  ⚠️  Ungültige Eingabe\n")


def compose_email(service: EmailService):
    """Interaktives Verfassen und Senden einer E-Mail."""
    print_header("✉️  Neue E-Mail verfassen")

    # Empfänger
    to = input("\n  An (Empfänger-Email): ").strip()
    if not to:
        print("  ⚠️  Kein Empfänger angegeben. Abgebrochen.\n")
        return

    # CC (optional)
    cc = input("  CC (optional, Enter zum Überspringen): ").strip()

    # Betreff
    subject = input("  Betreff: ").strip()
    if not subject:
        print("  ⚠️  Kein Betreff angegeben. Abgebrochen.\n")
        return

    # Format
    format_choice = input("  Format: [1] Plaintext (Standard)  [2] HTML\n  Wahl (Enter für Plaintext): ").strip()
    html_mode = format_choice == "2"

    # Nachrichtentext
    if html_mode:
        print("\n  HTML-Body eingeben (leere Zeile zum Beenden):")
    else:
        print("\n  Nachricht eingeben (leere Zeile zum Beenden):")

    lines = []
    while True:
        line = input("  > ")
        if line == "":
            break
        lines.append(line)

    body = "\n".join(lines)

    if not body.strip():
        print("  ⚠️  Leere Nachricht. Abgebrochen.\n")
        return

    # Vorschau
    print_section("📋 Vorschau")
    print(f"  An:      {to}")
    if cc:
        print(f"  CC:      {cc}")
    print(f"  Betreff: {subject}")
    print(f"  Format:  {'HTML' if html_mode else 'Plaintext'}")
    print(f"\n  Nachricht:")
    preview = body[:300]
    for line in preview.split("\n"):
        print(f"    {line}")
    if len(body) > 300:
        print(f"    [...{len(body) - 300} weitere Zeichen...]")
    print()

    # Bestätigung
    confirm = input("  Senden? (ja/nein): ").strip().lower()
    if confirm not in ("ja", "yes", "y"):
        print("  ❌ Abgebrochen.\n")
        return

    try:
        result = service.send(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            html=html_mode,
        )
        print(f"\n  ✅ E-Mail erfolgreich gesendet!")
        print(f"     Message-ID: {result.get('id', 'n/a')}")
        print(f"     {result.get('message', '')}\n")
    except ValueError as e:
        print(f"\n  ❌ Validierungsfehler: {e}\n")
    except Exception as e:
        print(f"\n  ❌ Fehler beim Senden: {e}\n")


def main_menu(service: EmailService):
    """Zeigt das Hauptmenü."""
    print_header("📮 Gmail Automation Tool")
    
    labels = service.get_labels(use_cache=False)
    
    print("\n  Hauptmenü:")
    print("    [1] Profil anzeigen")
    print("    [2] Labels/Ordner anzeigen")
    print("    [3] E-Mails in einem Ordner auflisten")
    print("    [4] E-Mails nach Absender filtern")
    print("    [5] Letzte 5 E-Mails aus Posteingang")
    print("    [6] Alle E-Mails in einem Ordner endgültig löschen")
    print("    [7] Labels verwalten (Neu erstellen / Umbenennen)")
    print("    [8] 🤖 KI: E-Mails auf Job-Angebote prüfen und wegsortieren")
    print("    [9] 📋 Alle Absender in einem Ordner auflisten")
    print("    [10] 🔍 Volltextsuche in E-Mails")
    print("    [11] ✉️  Neue E-Mail verfassen und senden")
    print("    [0] Beenden")
    
    choice = input("\n  Wahl eingeben: ").strip()
    
    if choice == "1":
        show_profile(service)
    
    elif choice == "2":
        show_labels(service)
    
    elif choice == "3":
        result = menu_select_label(labels)
        if result:
            label_id, label_name = result
            show_label_emails(service, label_id, label_name)
            folder_actions(service, label_id, label_name)
    
    elif choice == "4":
        result = menu_select_label(labels)
        if result:
            label_id, label_name = result
            filter_emails_by_sender(service, label_id, label_name)
    
    elif choice == "5":
        print_header("📧 Letzte 5 E-Mails im Posteingang")
        emails = service.get_inbox(max_results=5)
        for i, email in enumerate(emails, 1):
            status = "[🔴 NEU]" if email.is_unread else "[   ]"
            print(f"  {status} {i}. {email.subject[:55]}")
            print(f"       Von:   {email.sender[:50]}")
            print(f"       Datum: {email.date}")
            print()

    elif choice == "6":
        delete_all_emails_in_folder(service)
    
    elif choice == "7":
        print_header("🏷️ Labels verwalten")
        print("  [1] Neues Label erstellen")
        print("  [2] Bestehendes Label umbenennen")
        sub_choice = input("\n  Wahl eingeben: ").strip()
        
        if sub_choice == "1":
            new_name = input("  Name des neuen Labels: ").strip()
            if new_name:
                try:
                    service.create_label(new_name)
                    print(f"\n  ✅ Label '{new_name}' erfolgreich erstellt!\n")
                    labels = service.get_labels(use_cache=False)
                except Exception as e:
                    print(f"\n  ❌ Fehler: {e}\n")
        elif sub_choice == "2":
            custom_labels = [l for l in labels if l["id"] not in [v[0] for v in COMMON_LABELS.values()]]
            if custom_labels:
                print("\n  Verfügbare Labels:")
                for i, lbl in enumerate(custom_labels, 1):
                    print(f"    [{i}] {lbl['name']}")
                lbl_choice = input("\n  Label-Nummer zum Umbenennen eingeben: ").strip()
                try:
                    idx = int(lbl_choice) - 1
                    if 0 <= idx < len(custom_labels):
                        target_id = custom_labels[idx]["id"]
                        old_name = custom_labels[idx]["name"]
                        new_name = input(f"  Neuer Name für '{old_name}' (z.B. Job_angebot): ").strip()
                        if new_name:
                            service.rename_label(target_id, new_name)
                            print(f"\n  ✅ Label in '{new_name}' umbenannt!\n")
                            labels = service.get_labels(use_cache=False)
                except (ValueError, IndexError):
                    print("  ⚠️  Ungültige Wahl\n")
            else:
                print("  ⚠️  Keine benutzerdefinierten Labels vorhanden\n")
        else:
            print("  ⚠️  Ungültige Wahl\n")
            
    elif choice == "8":
        print_header("🤖 KI Job-Agent – Automatische E-Mail-Sortierung")
        print("  Dieser Assistent sucht nach E-Mails von Job-Portalen und sortiert")
        print("  sie automatisch in die passenden Ordner:\n")
        print("    📁 Job_Empfehlungen       → Stellenanzeigen, Jobalarms, neue Stellen")
        print("    📁 Einladung              → Zusagen, Interview-Einladungen")
        print("    📁 Absage                 → Ablehnungen, Absagen")
        print("    📁 Gesendete_Bewerbungen  → Bewerbung eingegangen / bestätigt")
        print()

        # Standard-Absender oder benutzerdefiniert
        default_senders = "indeed, stepstone, heyjobs"
        senders = input(f"  Absender (Enter für '{default_senders}'): ").strip()
        if not senders:
            senders = default_senders

        # ─── Labels sicherstellen ─────────────────────────────────────
        REQUIRED_LABELS = {
            "EMPFEHLUNG":    "Job_Empfehlungen",
            "EINLADUNG":     "Einladung",
            "ABSAGE":        "Absage",
            "BESTAETIGUNG":  "Gesendete_Bewerbungen",
        }

        labels = service.get_labels(use_cache=False)
        label_map = {}  # Kategorie -> Label-ID

        for category, label_name in REQUIRED_LABELS.items():
            label_id = None
            for lbl in labels:
                if lbl["name"].lower() == label_name.lower():
                    label_id = lbl["id"]
                    break

            if not label_id:
                print(f"  ⚠️  Label '{label_name}' existiert noch nicht. Wird erstellt...")
                try:
                    new_lbl = service.create_label(label_name)
                    label_id = new_lbl["id"]
                    print(f"  ✅ Label '{label_name}' erstellt.")
                except Exception as e:
                    print(f"  ❌ Fehler beim Erstellen von '{label_name}': {e}")
                    return True

            label_map[category] = label_id

        print()

        # ─── E-Mails suchen ──────────────────────────────────────────
        query = sender_query(senders)
        print(f"  🔍 Suche im Posteingang nach E-Mails von: {senders}...")

        final_query = f"in:inbox {query}"
        matching_emails = service.get_inbox(max_results=50, query=final_query)

        if not matching_emails:
            print("  ℹ️  Keine E-Mails von diesen Absendern im Posteingang gefunden.\n")
            return True

        print(f"  ✅ {len(matching_emails)} E-Mails gefunden. Starte KI-Klassifizierung...\n")

        # ─── KI-Klassifizierung ───────────────────────────────────────
        from gmail_bot.agent.job_classifier import classify_job_email
        import asyncio

        counters = {"EMPFEHLUNG": 0, "EINLADUNG": 0, "ABSAGE": 0, "BESTAETIGUNG": 0, "IRRELEVANT": 0}
        ICONS = {
            "EMPFEHLUNG":    "💼",
            "EINLADUNG":     "🎉",
            "ABSAGE":        "📭",
            "BESTAETIGUNG":  "✉️",
            "IRRELEVANT":    "⏭️",
        }

        for i, email_summary in enumerate(matching_emails, 1):
            snippet = email_summary.snippet
            subject = email_summary.subject

            print(f"  [{i}/{len(matching_emails)}] {subject[:55]}")

            # KI-Klassifizierung
            try:
                category = asyncio.run(classify_job_email(subject, snippet))
            except Exception as e:
                print(f"      -> ❌ KI-Fehler: {e}")
                counters["IRRELEVANT"] += 1
                continue

            icon = ICONS.get(category, "❓")

            if category in label_map:
                target_label = REQUIRED_LABELS[category]
                service.batch_move_to_label(
                    [email_summary.id],
                    label_map[category],
                    remove_label_id="INBOX"
                )
                print(f"      -> {icon} {category} → verschoben nach '{target_label}'")
            else:
                print(f"      -> {icon} IRRELEVANT → bleibt im Posteingang")

            counters[category] += 1

        # ─── Zusammenfassung ──────────────────────────────────────────
        print_header("📊 Zusammenfassung")
        print(f"  💼 Job-Empfehlungen:       {counters['EMPFEHLUNG']:>3} → Ordner 'Job_Empfehlungen'")
        print(f"  🎉 Einladungen:            {counters['EINLADUNG']:>3} → Ordner 'Einladung'")
        print(f"  📭 Absagen:                {counters['ABSAGE']:>3} → Ordner 'Absage'")
        print(f"  ✉️  Bewerbungsbestätigungen: {counters['BESTAETIGUNG']:>3} → Ordner 'Gesendete_Bewerbungen'")
        print(f"  ⏭️  Irrelevant:              {counters['IRRELEVANT']:>3} → Posteingang (unverändert)")
        total_moved = counters['EMPFEHLUNG'] + counters['EINLADUNG'] + counters['ABSAGE'] + counters['BESTAETIGUNG']
        print(f"\n  ✅ Insgesamt {total_moved} E-Mails automatisch sortiert.\n")

    elif choice == "9":
        show_all_senders(service, labels)

    elif choice == "10":
        fulltext_search_menu(service)

    elif choice == "11":
        compose_email(service)

    elif choice == "0":
        print("\n  👋 Auf Wiedersehen!\n")
        return False
    
    else:
        print(f"  ⚠️  Ungültige Wahl: '{choice}'\n")
    
    return True


def main():
    """Hauptfunktion mit interaktivem Menü."""
    # Service initialisieren (OAuth2-Login beim ersten Mal)
    service = EmailService()
    
    # Labels laden
    labels = service.get_labels(use_cache=True)
    
    # Interaktive Schleife
    while True:
        if not main_menu(service):
            break


if __name__ == "__main__":
    main()
