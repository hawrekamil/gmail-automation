#!/usr/bin/env python3
"""
Perplexity Agent CLI – Interaktives Kommandozeilen-Interface.

Ermöglicht die Interaktion mit verschiedenen Perplexity-Agenten
über die Kommandozeile mit Fehlerbehandlung und Logging.

Verwendung:
    python main.py                    # Interaktiver Modus (Job Assistant)
    python main.py --agent general    # Mit Allgemein-Agent
    python main.py --query "Frage"    # Einzelne Abfrage
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Windows-Konsole auf UTF-8 umstellen (für Emojis in Ausgaben)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from my_agent.agent import create_agent, call_agent_async, AGENT_CONFIGS

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text: str):
    """Gibt einen formatierten Header aus."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_section(text: str):
    """Gibt einen formatierten Section-Header aus."""
    print("\n" + "-" * 70)
    print(f"  {text}")
    print("-" * 70 + "\n")


async def run_interactive_mode(agent_type: str):
    """
    Startet den interaktiven Modus.
    
    Args:
        agent_type: Typ des Agents
    """
    print_header(f"🤖 Perplexity Agent – {agent_type.upper()}")
    print("📝 Gib deine Fragen ein (Ctrl+C oder 'exit' zum Beenden)\n")
    
    agent = create_agent(agent_type)
    session_id = 0
    
    try:
        while True:
            try:
                user_input = input("Du: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print_section("Auf Wiedersehen! 👋")
                    break
                
                session_id += 1
                response = await call_agent_async(
                    agent,
                    user_input,
                    session_id=f"session_{session_id}"
                )
                
                if response:
                    print(f"\n🤖 Agent:\n{response}\n")
                else:
                    print("❌ Fehler: Keine Antwort vom Agent erhalten.\n")
                    
            except KeyboardInterrupt:
                print_section("Unterbrochen. Auf Wiedersehen! 👋")
                break
                
    except Exception as e:
        logger.error(f"Fehler im interaktiven Modus: {str(e)}", exc_info=True)
        sys.exit(1)


async def run_single_query(query: str, agent_type: str):
    """
    Führt eine einzelne Abfrage aus.
    
    Args:
        query: Die Abfrage
        agent_type: Typ des Agents
    """
    print_header("🤖 Perplexity Agent")
    print(f"📝 Abfrage: {query}\n")
    
    try:
        agent = create_agent(agent_type)
        response = await call_agent_async(agent, query)
        
        if response:
            print_section("Agent Antwort")
            print(response)
        else:
            logger.error("Keine Antwort vom Agent erhalten")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fehler: {str(e)}", exc_info=True)
        sys.exit(1)


def main():
    """Haupteinstiegspunkt."""
    parser = argparse.ArgumentParser(
        description="Perplexity Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Verfügbare Agents:
  - job_assistant     Bewerbungs- und Karriereberater
  - general           Allgemeiner Assistent

Beispiele:
  python main.py
  python main.py --agent general
  python main.py --query "Wie schreibe ich ein Anschreiben?"
        """
    )
    
    parser.add_argument(
        "--agent",
        choices=list(AGENT_CONFIGS.keys()),
        default="job_assistant",
        help="Agent-Typ (default: job_assistant)"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Einzelne Abfrage (wenn nicht gesetzt: interaktiver Modus)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.query:
            # Einzelne Abfrage
            asyncio.run(run_single_query(args.query, args.agent))
        else:
            # Interaktiver Modus
            asyncio.run(run_interactive_mode(args.agent))
    
    except KeyboardInterrupt:
        print("\n\n👋 Beendet")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Kritischer Fehler: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

