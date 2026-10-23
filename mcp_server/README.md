# Gmail Automation MCP Server 🔌

Ein MCP-Server (Model Context Protocol), der die Gmail-Automatisierungsfunktionen
als Tools für KI-Agenten bereitstellt.

## Verfügbare Tools

| Tool | Beschreibung |
|---|---|
| `list_inbox` | E-Mails im Posteingang auflisten (mit optionalem Suchfilter) |
| `generate_application` | Bewerbungsanschreiben per KI (Perplexity) generieren |
| `send_application` | E-Mail senden, optional mit Lebenslauf als PDF-Anhang |
| `classify_email` | Job-E-Mails automatisch kategorisieren (Empfehlung/Einladung/Absage/...) |

## Voraussetzungen

- Gmail OAuth2 eingerichtet (`config/credentials.json` + `config/token.json`)
- Perplexity API Key in `perplexity_agent/my_agent/.env`
- Virtuelle Umgebung mit allen Abhängigkeiten

## Starten

```bash
# Aus dem Hauptverzeichnis (gmail_automation_project/)
.\venv\Scripts\python.exe mcp_server/server.py
```

## Konfiguration für AI-Clients

### Cursor / Antigravity / Claude Desktop

Füge folgendes in die MCP-Konfiguration deines Clients ein:

```json
{
    "mcpServers": {
        "gmail-automation": {
            "command": "C:/Users/HAWRE/google-cloud-projects/gmail_automation_project/venv/Scripts/python.exe",
            "args": ["C:/Users/HAWRE/google-cloud-projects/gmail_automation_project/mcp_server/server.py"]
        }
    }
}
```

### Page-Agent Integration

Der MCP-Server kann zusammen mit der Page-Agent Chrome Extension genutzt werden:

1. Page-Agent Chrome Extension installieren
2. Page-Agent MCP-Server starten (`npx @page-agent/mcp`)
3. Beide MCP-Server in deinem AI-Client konfigurieren
4. Der AI-Client kann dann sowohl den Browser steuern als auch E-Mails senden

## Architektur

```
┌──────────────────┐         ┌──────────────────────┐         ┌──────────────┐
│  AI Client       │  stdio  │  gmail-automation     │         │  Gmail API   │
│  (Claude/Cursor/ │◄──────►│  MCP Server (Python)   │◄──────►│  (Google)    │
│   Page-Agent)    │  (MCP)  │                        │         │              │
└──────────────────┘         │  Tools:                │         └──────────────┘
                             │  - list_inbox          │
                             │  - generate_application│──►  Perplexity AI
                             │  - send_application    │
                             │  - classify_email      │
                             └──────────────────────┘
```