# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Perplexity Agent – Konfiguration und Verwaltung.

Stellt flexible Agent-Konfiguration mit verschiedenen Rollen bereit.
"""

from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from the my_agent directory
current_dir = Path(__file__).parent
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)

# ─── Konfiguration ────────────────────────────────────────────────────────

MODEL = os.getenv("AGENT_MODEL", "sonar-pro")
TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))

# ─── Agent Definitionen ────────────────────────────────────────────────────

AGENT_CONFIGS = {
    "job_assistant": {
        "name": "job_application_assistant",
        "description": "Ein Agent für Bewerbungen und Karriereberatung",
        "instruction": """# Rolle & Identität
Du bist ein professioneller und ermutigender Karriereberater und Experte für das Schreiben von Bewerbungen. Deine Aufgabe ist es, dem Nutzer dabei zu helfen, herausragende Anschreiben, Lebensläufe und Motivationsschreiben zu erstellen.

# Deine Aufgaben
1. **Bewerbungen optimieren:** Überarbeite Texte des Nutzers, um sie professioneller, überzeugender und fehlerfrei zu machen.
2. **Struktur vorgeben:** Hilf dem Nutzer, seine Erfahrungen passend zur Stellenanzeige zu strukturieren.
3. **Ideen liefern:** Wenn der Nutzer nicht weiß, wie er anfangen soll, gib ihm gute Formulierungsvorschläge oder ein Gerüst für sein Anschreiben.
4. **Feedback geben:** Kritisiere konstruktiv und erkläre, warum eine bestimmte Formulierung im Geschäftsumfeld besser ankommt.

# Kommunikationsstil
- Sprache: Deutsch (professionell und höflich)
- Ton: Motivierend, klar und zielgerichtet
- Vermeide Standardfloskeln. Fokussiere dich auf moderne, individuelle Formulierungen."""
    },
    "general": {
        "name": "general_assistant",
        "description": "Ein vielseitiger KI-Assistent",
        "instruction": """Du bist ein hilfreicher, freundlicher und sachkundiger KI-Assistent. 
Antworte präzise, höflich und informativ auf Fragen."""
    }
}

# ─── Agent-Verwaltung ──────────────────────────────────────────────────────

def create_agent(agent_type: str = "job_assistant") -> Dict[str, Any]:
    """
    Erstellt einen konfigurierten Agent.
    
    Args:
        agent_type: Typ des Agents ('job_assistant', 'general')
    
    Returns:
        Konfigurierter Agent (als Dictionary für Perplexity Parameter)
    
    Raises:
        ValueError: Wenn agent_type unbekannt ist
    """
    if agent_type not in AGENT_CONFIGS:
        raise ValueError(f"Unbekannter Agent-Typ: {agent_type}. Verfügbar: {list(AGENT_CONFIGS.keys())}")
    
    config = AGENT_CONFIGS[agent_type]
    
    agent = {
        "name": config["name"],
        "model": MODEL,
        "description": config["description"],
        "instruction": config["instruction"]
    }
    
    logger.info(f"Agent '{agent_type}' erstellt (Modell: {MODEL})")
    return agent


async def call_agent_async(
    agent: Dict[str, Any],
    query: str,
    app_name: str = "perplexity_agent",
    user_id: str = "default_user",
    session_id: str = "default_session"
) -> Optional[str]:
    """
    Ruft den Agent asynchron auf und gibt die Antwort zurück.
    
    Args:
        agent: Das zu verwendende Agent-Dictionary
        query: Die Nutzerfrage
        app_name: Name der Anwendung
        user_id: Benutzer-ID
        session_id: Session-ID
    
    Returns:
        Agent-Antwort oder None bei Fehler
    """
    try:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        client = AsyncOpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        
        logger.info(f"Anfrage an Agent: {query[:100]}...")
        
        messages = [
            {"role": "system", "content": agent.get("instruction", "")},
            {"role": "user", "content": query}
        ]
        
        response = await client.chat.completions.create(
            model=agent.get("model", MODEL),
            messages=messages,
            temperature=TEMPERATURE,
        )
        
        response_text = response.choices[0].message.content
        if response_text:
            logger.info("Agent-Antwort erhalten")
            return response_text
        else:
            logger.warning("Keine Antwort vom Agent erhalten")
            return None
            
    except Exception as e:
        logger.error(f"Fehler beim Agent-Aufruf: {str(e)}", exc_info=True)
        return None


# ─── Synchrone Wrapper ────────────────────────────────────────────────────

def call_agent_sync(
    query: str,
    agent_type: str = "job_assistant",
    user_id: str = "default_user"
) -> Optional[str]:
    """
    Synchrone Wrapper-Funktion für Agent-Aufrufe.
    
    Args:
        query: Die Nutzerfrage
        agent_type: Typ des Agents
        user_id: Benutzer-ID
    
    Returns:
        Agent-Antwort oder None
    """
    agent = create_agent(agent_type)
    return asyncio.run(call_agent_async(agent, query, user_id=user_id))