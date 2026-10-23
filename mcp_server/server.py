"""
Gmail Automation MCP Server.

Stellt die Gmail-Automatisierungsfunktionen als MCP-Tools bereit,
sodass KI-Agenten (Page-Agent, Claude Desktop, Cursor, etc.)
E-Mails senden, lesen und Bewerbungen automatisieren koennen.

Verwendung:
    python -m mcp_server.server              # Starte den MCP-Server (stdio)
    python mcp_server/server.py              # Alternativ direkt

Tools:
    - list_inbox:            E-Mails im Posteingang auflisten
    - generate_application:  Anschreiben per KI generieren
    - send_application:      Bewerbungs-E-Mail senden (mit optionalem Anhang)
    - classify_email:        Job-E-Mail klassifizieren
"""

import sys
import asyncio
import base64
import mimetypes
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Projektroot zum Python-Path hinzufuegen
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

# ─── MCP Server erstellen ────────────────────────────────────────────────────

mcp = FastMCP(
    "gmail-automation",
    instructions=(
        "Gmail Automation Server. Bietet Tools zum Lesen und Senden von E-Mails, "
        "zum Generieren von Bewerbungsanschreiben per KI (Perplexity), und "
        "zum Klassifizieren von Job-E-Mails."
    ),
)

# ─── Pfad zu Bewerbungsunterlagen ─────────────────────────────────────────────

_CV_DIR = _PROJECT_ROOT / "Bewerbung Unterlagen"

# ─── Tool 1: Posteingang lesen ────────────────────────────────────────────────


@mcp.tool()
def list_inbox(max_results: int = 10, query: str = "") -> str:
    """Listet E-Mails im Gmail-Posteingang auf.

    Args:
        max_results: Maximale Anzahl (1-50, Standard: 10).
        query: Optionaler Gmail-Suchfilter (z.B. 'is:unread', 'from:firma.de').

    Returns:
        Formatierte Liste der E-Mails mit Absender, Betreff und Datum.
    """
    from gmail_bot.services import EmailService

    service = EmailService()
    max_results = max(1, min(max_results, 50))
    emails = service.get_inbox(max_results=max_results, query=query)

    if not emails:
        return "Keine E-Mails gefunden."

    lines = [f"📧 {len(emails)} E-Mail(s) im Posteingang:\n"]
    for i, email in enumerate(emails, 1):
        status = "🔴 NEU" if email.is_unread else "   "
        lines.append(f"[{status}] {i}. {email.subject}")
        lines.append(f"    Von:   {email.sender}")
        lines.append(f"    Datum: {email.date}")
        lines.append("")

    return "\n".join(lines)


# ─── Tool 2: Anschreiben generieren ──────────────────────────────────────────


@mcp.tool()
async def generate_application(
    company: str,
    job_title: str,
    requirements: str = "",
    extra_info: str = "",
) -> str:
    """Generiert ein professionelles Bewerbungsanschreiben per KI (Perplexity).

    Args:
        company: Name der Firma.
        job_title: Titel der Stelle (z.B. 'IT-Systemadministrator').
        requirements: Anforderungen aus der Stellenanzeige (optional).
        extra_info: Zusaetzliche Hinweise fuer das Anschreiben (optional).

    Returns:
        Das generierte Anschreiben als Text.
    """
    from gmail_bot.agent.career_agent import call_career_agent

    prompt_parts = [
        f"Bitte schreibe ein professionelles Bewerbungsanschreiben.",
        f"Firma: {company}",
        f"Stelle: {job_title}",
    ]
    if requirements:
        prompt_parts.append(f"Anforderungen: {requirements}")
    if extra_info:
        prompt_parts.append(f"Zusaetzliche Informationen: {extra_info}")

    prompt_parts.append(
        "Der Bewerber heisst Hawre Kamil und ist IT-Systemadministrator. "
        "Erstelle ein vollstaendiges, versandfertiges Anschreiben auf Deutsch."
    )

    query = "\n".join(prompt_parts)
    result = await call_career_agent(query)

    if not result:
        return "Fehler: Kein Anschreiben konnte generiert werden."

    return f"✅ Anschreiben generiert:\n\n{result}"


# ─── Tool 3: Bewerbung senden ────────────────────────────────────────────────


@mcp.tool()
def send_application(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    attach_cv: bool = False,
) -> str:
    """Sendet eine Bewerbungs-E-Mail ueber Gmail, optional mit Lebenslauf als Anhang.

    Args:
        to: Empfaenger-E-Mail-Adresse.
        subject: Betreff der E-Mail (z.B. 'Bewerbung als IT-Systemadministrator').
        body: Der vollstaendige E-Mail-Text (das Anschreiben).
        cc: CC-Empfaenger (optional).
        attach_cv: Wenn True, wird der Lebenslauf (PDF) als Anhang beigefuegt.

    Returns:
        Bestaetigungsnachricht mit Message-ID.
    """
    from gmail_bot.services import EmailService

    service = EmailService()

    if attach_cv:
        # E-Mail mit Anhang senden (MIME multipart)
        result = _send_with_attachment(service, to, subject, body, cc)
    else:
        # Einfache E-Mail senden
        result = service.send(to=to, subject=subject, body=body, cc=cc)

    return (
        f"✅ E-Mail erfolgreich gesendet!\n"
        f"   An: {to}\n"
        f"   Betreff: {subject}\n"
        f"   Message-ID: {result.get('id', 'n/a')}"
    )


def _send_with_attachment(
    service, to: str, subject: str, body: str, cc: str = ""
) -> dict:
    """Sendet eine E-Mail mit PDF-Anhang (Lebenslauf)."""
    # Lebenslauf finden
    cv_files = list(_CV_DIR.glob("*Lebenslauf*"))
    if not cv_files:
        cv_files = list(_CV_DIR.glob("*.pdf"))

    if not cv_files:
        # Fallback: ohne Anhang senden
        return service.send(to=to, subject=subject, body=body, cc=cc)

    cv_path = cv_files[0]

    # MIME Multipart erstellen
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc

    # Text-Teil
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # PDF-Anhang
    content_type, _ = mimetypes.guess_type(str(cv_path))
    if content_type is None:
        content_type = "application/octet-stream"
    main_type, sub_type = content_type.split("/", 1)

    with open(cv_path, "rb") as f:
        attachment = MIMEBase(main_type, sub_type)
        attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition", "attachment", filename=cv_path.name
    )
    msg.attach(attachment)

    # Senden ueber die Gmail API
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    client = service._client
    sent = (
        client._service.users()
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )

    return {
        "id": sent.get("id", ""),
        "thread_id": sent.get("threadId", ""),
        "message": f"E-Mail mit Anhang ({cv_path.name}) gesendet an {to}",
    }


# ─── Tool 4: E-Mail klassifizieren ──────────────────────────────────────────


@mcp.tool()
async def classify_email(subject: str, snippet: str) -> str:
    """Klassifiziert eine E-Mail in eine Job-Kategorie per KI.

    Kategorien:
        - EMPFEHLUNG:   Stellenanzeigen, Job-Empfehlungen
        - EINLADUNG:    Zusagen, Interview-Einladungen
        - ABSAGE:       Ablehnungen
        - BESTAETIGUNG: Bewerbung eingegangen
        - IRRELEVANT:   Newsletter, Werbung, etc.

    Args:
        subject: Der Betreff der E-Mail.
        snippet: Ein kurzer Textausschnitt der E-Mail.

    Returns:
        Die Kategorie und eine kurze Erklaerung.
    """
    from gmail_bot.agent.job_classifier import classify_job_email

    category = await classify_job_email(subject, snippet)

    labels = {
        "EMPFEHLUNG": "📋 Stellenanzeige / Job-Empfehlung",
        "EINLADUNG": "🎉 Einladung zum Vorstellungsgespraech",
        "ABSAGE": "❌ Absage auf Bewerbung",
        "BESTAETIGUNG": "📩 Bewerbungsbestaetigung",
        "IRRELEVANT": "📭 Nicht job-relevant",
    }

    description = labels.get(category, "Unbekannt")
    return f"Kategorie: {category}\n{description}\n\nBetreff: {subject}"


# ─── Einstiegspunkt ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
