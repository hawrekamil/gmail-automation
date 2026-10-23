import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load .env from perplexity_agent/my_agent/ directory
_AGENT_ENV = Path(__file__).parent.parent.parent / "perplexity_agent" / "my_agent" / ".env"
load_dotenv(dotenv_path=_AGENT_ENV)

APP_NAME = "gmail_career_agent"
USER_ID = "gmail_user"
SESSION_ID = "session_1"

APPLICATION_ASSISTANT_INSTRUCTION = """
# Rolle & Identität
Du bist ein professioneller und ermutigender Karriereberater und Experte für das Schreiben von Bewerbungen. Deine Aufgabe ist es, dem Nutzer dabei zu helfen, herausragende Anschreiben, Lebensläufe und Motivationsschreiben zu erstellen.

# Deine Aufgaben
1. **Bewerbungen optimieren:** Überarbeite Texte des Nutzers, um sie professioneller, überzeugender und fehlerfrei zu machen.
2. **Struktur vorgeben:** Hilf dem Nutzer, seine Erfahrungen passend zur Stellenanzeige zu strukturieren.
3. **Ideen liefern:** Wenn der Nutzer nicht weiß, wie er anfangen soll, gib ihm gute Formulierungsvorschläge oder ein Gerüst für sein Anschreiben.
4. **Feedback geben:** Kritisiere konstruktiv und erkläre, warum eine bestimmte Formulierung im Geschäftsumfeld besser ankommt.

# Kommunikationsstil
- Sprache: Deutsch (professionell und höflich)
- Ton: Motivierend, klar und zielgerichtet
- Vermeide Standardfloskeln. Fokussiere dich auf moderne, individuelle Formulierungen.
"""

async def call_career_agent(query: str) -> str:
    """Sendet eine Anfrage an den Karriere-Agenten (Perplexity) und gibt die Antwort zurück."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    client = AsyncOpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    
    messages = [
        {"role": "system", "content": APPLICATION_ASSISTANT_INSTRUCTION},
        {"role": "user", "content": query}
    ]
    
    response = await client.chat.completions.create(
        model=os.getenv("AGENT_MODEL", "sonar-pro"),
        messages=messages,
        temperature=0.7,
    )
            
    response_text = response.choices[0].message.content
    return response_text if response_text else ""

if __name__ == "__main__":
    test_query = "Ich möchte mich als Softwareentwickler bewerben. Kannst du mir ein kurzes Anschreiben entwerfen?"
    print(f"User Query: {test_query}\n")
    response = asyncio.run(call_career_agent(test_query))
    print(f"Agent Response:\n{response}")
