"""
KI-basierter E-Mail-Klassifizierer für Job-bezogene E-Mails.

Klassifiziert E-Mails in 5 Kategorien:
  - EMPFEHLUNG:    Stellenanzeigen, Job-Empfehlungen, neue Jobangebote
  - EINLADUNG:     Zusagen, Einladungen zum Vorstellungsgespraech
  - ABSAGE:        Ablehnungen, Absagen auf Bewerbungen
  - BESTAETIGUNG:  Bewerbungsbestaetigung, Bewerbung eingegangen
  - IRRELEVANT:    Newsletter, Werbung, Profil-Updates, Spam
"""

import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load .env from perplexity_agent/my_agent/ directory
_AGENT_ENV = Path(__file__).parent.parent.parent / "perplexity_agent" / "my_agent" / ".env"
load_dotenv(dotenv_path=_AGENT_ENV)


CLASSIFIER_INSTRUCTION = """
Du bist ein präziser E-Mail-Klassifizierungs-Assistent für Job-bezogene E-Mails.

Deine Aufgabe ist es, den Betreff und den Textausschnitt (Snippet) einer E-Mail zu lesen und sie in GENAU EINE der folgenden Kategorien einzuordnen:

1. EMPFEHLUNG – Die E-Mail enthält eine Stellenanzeige, eine Job-Empfehlung, einen Jobalarm, 
   neue passende Stellen oder ein konkretes Jobangebot von einem Job-Portal 
   (z.B. "Neue Jobs für Sie", "Passende Stellen", "Job-Empfehlung", "Jobalarm").

2. EINLADUNG – Die E-Mail enthält eine POSITIVE Antwort auf eine Bewerbung: 
   eine Einladung zum Vorstellungsgespräch, eine Zusage, ein Terminvorschlag für ein Interview, 
   oder eine Bitte um ein Kennenlerngespräch 
   (z.B. "Einladung zum Gespräch", "Wir möchten Sie kennenlernen", "Interview-Termin").

3. ABSAGE – Die E-Mail enthält eine NEGATIVE Antwort auf eine Bewerbung: 
   eine Ablehnung, eine Absage, eine Benachrichtigung dass die Stelle anderweitig besetzt wurde 
   (z.B. "Leider müssen wir Ihnen absagen", "anderweitig besetzt", "nicht berücksichtigen").

4. BESTAETIGUNG – Die E-Mail ist eine Bestätigung, dass eine Bewerbung eingegangen ist, 
   oder informiert darüber, dass sich der Nutzer erfolgreich auf eine Stelle beworben hat. 
   Es handelt sich um eine reine Eingangsbestätigung, NICHT um eine Zusage oder Absage 
   (z.B. "Ihre Bewerbung ist eingegangen", "Vielen Dank für Ihre Bewerbung", 
   "Sie haben sich beworben", "Bewerbung erfolgreich gesendet", "Wir haben Ihre Bewerbung erhalten").

5. IRRELEVANT – Alles andere: Newsletter ohne Job-Bezug, Werbung, Profil-Updates, 
   Kontobenachrichtigungen, Passwort-Resets, allgemeine Marketing-E-Mails.

Antworte AUSSCHLIESSLICH mit EINEM dieser fünf Wörter: EMPFEHLUNG, EINLADUNG, ABSAGE, BESTAETIGUNG oder IRRELEVANT
Keine Erklärungen. Kein anderer Text.
"""


async def classify_job_email(subject: str, snippet: str) -> str:
    """
    Klassifiziert eine E-Mail per KI (Perplexity) in eine Job-Kategorie.

    Args:
        subject: Betreff der E-Mail.
        snippet: Kurzer Textausschnitt.

    Returns:
        Eine der Kategorien: 'EMPFEHLUNG', 'EINLADUNG', 'ABSAGE' oder 'IRRELEVANT'.
    """
    query = f"Betreff: {subject}\nText: {snippet}"

    api_key = os.getenv("PERPLEXITY_API_KEY")
    client = AsyncOpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    messages = [
        {"role": "system", "content": CLASSIFIER_INSTRUCTION},
        {"role": "user", "content": query}
    ]

    response = await client.chat.completions.create(
        model=os.getenv("AGENT_MODEL", "sonar"),
        messages=messages,
        temperature=0.1,
    )

    response_text = response.choices[0].message.content
    result = response_text.strip().upper() if response_text else "IRRELEVANT"

    # Sicherstellen, dass nur gültige Kategorien zurückkommen
    valid = {"EMPFEHLUNG", "EINLADUNG", "ABSAGE", "BESTAETIGUNG", "IRRELEVANT"}
    if result not in valid:
        return "IRRELEVANT"

    return result


# Abwärtskompatibilität
async def check_if_job_offer(subject: str, snippet: str) -> bool:
    """Legacy-Funktion: Prüft ob die E-Mail ein Jobangebot ist."""
    category = await classify_job_email(subject, snippet)
    return category in ("EMPFEHLUNG", "EINLADUNG")
