# 📧 Gmail Automation Suite & AI Agent 🤖

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Protocol: MCP](https://img.shields.io/badge/Protocol-MCP-purple.svg)](https://modelcontextprotocol.io/)

Ein modulares, performantes Python-System zur vollständigen **Gmail-Automatisierung** über die offizielle Google Gmail API, kombiniert mit **KI-gestützter E-Mail-Klassifizierung** (Perplexity AI) und einem standardisierten **MCP-Server (Model Context Protocol)**.

---

## 🌟 Highlights & Features

- ⚡ **Gmail API Integration**: Vollständiger OAuth 2.0 Auth-Flow, Token-Management und Refresh.
- 📦 **High-Performance Batch-Processing**: Bis zu 90% weniger API-Calls durch gebündelte Batch-Operationen (`mark_as_read`, `trash`, Labels, etc.).
- 🧠 **AI-basierte E-Mail-Klassifizierung**: Automatische Erkennung und Sortierung wichtiger E-Mails, Einladungen, Bestätigungen und Absagen (Perplexity AI).
- 🔌 **Model Context Protocol (MCP)**: Eigener MCP-Server zur direkten Anbindung an KI-Entwicklungsumgebungen und Agents (z.B. Claude Desktop, Cursor, Copilot).
- 💻 **Interaktives CLI**: Komfortable Befehlszeilen-Schnittstelle (`cli.py`, `main.py`) mit interaktivem Menü.
- 🛡️ **Sicherheit & Caching**: Automatische Token-Speicherung, Memory-Caching und strukturierter Logger.

---

## 🏗️ Architektur & Projektstruktur

```text
gmail_automation_project/
├── gmail_bot/                # Kernmodul
│   ├── agent/                # KI-Klassifizierer & Career-Agent (Perplexity)
│   ├── auth/                 # Google OAuth 2.0 Authentifizierung
│   ├── config/               # Settings & Konfigurationsmanagement
│   ├── core/                 # Gmail API Client & Exception Handling
│   ├── models/               # Datamodels (Email, Batch-Resultate)
│   ├── services/             # EmailService & High-Performance BatchProcessor
│   └── utils/                # Caching, Logging & Hilfsfunktionen
├── mcp_server/               # Standardisierter Model Context Protocol (MCP) Server
├── perplexity_agent/         # Standalone KI-Agenten & Recherchetools
├── tests/                    # Pytest Unit- & Integrationstests
├── cli.py                    # Vollwertige CLI-Schnittstelle
├── main.py                   # Haupteinstiegspunkt & interaktiver Workflow
├── examples.py               # Code-Beispiele zur Modulnutzung
├── pyproject.toml            # Paket- & Abhängigkeitsdefinition
└── .env.example              # Vorlage für Umgebungsvariablen
```

---

## 🚀 Schnellstart & Installation

### 1. Voraussetzungen

- Python >= 3.12
- Ein Google Cloud Projekt mit aktivierter **Gmail API**
- OAuth 2.0 Client-ID (`credentials.json` als Desktop-Anwendung herunterladen)

### 2. Repository klonen & Abhängigkeiten installieren

```bash
git clone https://github.com/hawrekamil/gmail-automation.git
cd gmail-automation

# Virtuelle Umgebung erstellen und aktivieren
python -m venv .venv
source .venv/bin/activate  # Unter Windows: .venv\Scripts\activate

# Abhängigkeiten installieren
pip install -e .
```

### 3. Umgebungsvariablen & Google Credentials einrichten

1. Kopiere die Vorlage:
   ```bash
   cp .env.example .env
   ```
2. Trage deinen `PERPLEXITY_API_KEY` (optional für KI-Features) in die `.env` ein.
3. Platziere deine aus der Google Cloud Console heruntergeladene Datei `credentials.json` im Verzeichnis `config/credentials.json` (oder direkt im Projektstamm).

---

## 📖 Verwendung

### Interaktiver Modus

Starte das interaktive Terminal-Menü:

```bash
python main.py
```
*Beim ersten Start öffnet sich automatisch das Browserfenster zur Google-Autorisierung. Der Token wird sicher lokal für Folgesitzungen zwischengespeichert.*

### CLI-Nutzung

```bash
# Ungelesene E-Mails auflisten
python cli.py list --unread --limit 10

# E-Mail senden
python cli.py send --to "empfaenger@example.com" --subject "Statusupdate" --body "Hallo, hier ist das Update."

# E-Mails automatisch nach Relevanz klassifizieren und sortieren
python main.py --classify
```

### Nutzung als Python-Bibliothek

```python
from gmail_bot.services import EmailService

service = EmailService()

# E-Mails mit Suchfilter abfragen
emails = service.get_inbox(query="from:github.com is:unread", max_results=5)
for email in emails:
    print(f"Betreff: {email.subject} | Von: {email.sender}")

# High-Performance Batch-Operation
batch_processor = service.get_batch_processor()
msg_ids = [e.id for e in emails]
result = batch_processor.mark_as_read(msg_ids)
print(f"Erfolgreich: {result.success}/{result.total}")
```

---

## 🔌 Model Context Protocol (MCP) Server

Der integrierte MCP-Server stellt KI-Modellen Werkzeuge für Gmail zur Verfügung:

```bash
python -m mcp_server.server
```

Verfügbare MCP-Tools:
- `list_inbox`: Posteingang durchsuchen und anzeigen
- `generate_application`: Perplexity AI-Anschreiben formulieren
- `send_application`: E-Mail mit optionalem PDF-Anhang versenden
- `classify_emails`: Automatische Kategorisierung & Labeling

---

## 🧪 Tests ausführen

```bash
pytest tests/ -v
```

---

## 🔒 Sicherheitshinweis

- **Niemals** `credentials.json`, `token.json` oder `.env`-Dateien committen.
- Alle Secrets und persönlichen Dokumente werden über [.gitignore](.gitignore) strikt gefiltert.

---

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.
