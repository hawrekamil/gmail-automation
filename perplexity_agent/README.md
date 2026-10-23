# Perplexity Agent für Gmail Automation 🤖

Ein KI-gestützter Agent basierend auf Perplexity AI (z.B. sonar-pro) zur Automatisierung und Optimierung von Gmail-Funktionen.

## Features

- **Job Application Assistant**: Hilft beim Verfassen und Optimieren von Bewerbungen
- **General Assistant**: Vielseitiger KI-Assistent für diverse Aufgaben
- **Asynchrone Verarbeitung**: Effiziente Verarbeitung von Anfragen
- **Google Search Integration**: Zugriff auf aktuelle Informationen
- **CLI Interface**: Einfache Kommandozeilen-Bedienung
- **Session Management**: Persistente Unterhaltungen
- **Umgebungsvariablen**: Flexible Konfiguration

## Installation

```bash
# Abhängigkeiten installieren
pip install -e .

# Mit Dev-Tools (für Testing, Linting)
pip install -e ".[dev]"
```

## Setup

1. **Perplexity API Key konfigurieren**

```bash
# .env Datei erstellen
echo 'PERPLEXITY_API_KEY=your_api_key_here' > .env
echo 'AGENT_MODEL=sonar-pro' >> .env
echo 'AGENT_TEMPERATURE=0.7' >> .env
```

2. **API Key abrufen**

Besuche [Perplexity API Einstellungen](https://www.perplexity.ai/settings/api) um einen API Key zu erstellen.

## Verwendung

### Kommandozeile (CLI)

#### Interaktiver Modus

```bash
python main.py
```

Startet den Bewerbungs-Assistenten und du kannst mehrere Fragen stellen.

#### Mit Allgemein-Agent

```bash
python main.py --agent general
```

#### Einzelne Abfrage

```bash
python main.py --query "Schreib mir ein Anschreiben für einen Python-Job"
```

#### Hilfe anzeigen

```bash
python main.py --help
```

### Python Code

#### Synchrone Verwendung

```python
from my_agent import call_agent_sync

response = call_agent_sync(
    query="Ich bin Softwareentwickler mit 5 Jahren Erfahrung",
    agent_type="job_assistant"
)

print(response)
```

#### Asynchrone Verwendung

```python
import asyncio
from my_agent import create_agent, call_agent_async

async def main():
    agent = create_agent("job_assistant")
    response = await call_agent_async(
        agent,
        "Kannst du mein Anschreiben verbessern?"
    )
    print(response)

asyncio.run(main())
```

## Konfiguration

### Umgebungsvariablen (.env)

```bash
# Erforderlich
GOOGLE_API_KEY=your_api_key_here

# Optional (mit Standardwerten)
AGENT_MODEL=gemini-2.0-flash          # AI-Modell
AGENT_TEMPERATURE=0.7                  # Kreativität (0.0-1.0)
SESSION_TIMEOUT=3600                   # Session-Timeout in Sekunden
```

## Agent-Typen

| Agent | Beschreibung | Verwendung |
|-------|-------------|----------|
| `job_assistant` | Bewerbungs- und Karriereberater | Anschreiben, Lebensläufe, Motivationsschreiben |
| `general` | Allgemeiner Assistent | Beliebige Fragen |

## Tests

```bash
# Alle Tests ausführen
pytest

# Mit Coverage Report
pytest --cov=my_agent

# Nur schnelle Tests
pytest -m "not slow"

# Verbose Output
pytest -vv
```

## Logging

Alle Aktivitäten werden in die Konsole geloggt:

```
2024-05-10 14:23:45,123 - my_agent.agent - INFO - Agent 'job_assistant' erstellt
2024-05-10 14:23:46,456 - my_agent.agent - INFO - Anfrage an Agent: Ich möchte...
2024-05-10 14:23:48,789 - my_agent.agent - INFO - Agent-Antwort erhalten
```

## Lizenz

Apache License 2.0

## Weitere Informationen

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Dokumentation](https://ai.google.dev/docs)
- [Google ADK Dokumentation](https://github.com/googleapis/python-cloud-adk)
