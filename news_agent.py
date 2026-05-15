import requests
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()


client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


def analizza_notizie_con_claude(notizie, argomento):
    """Claude analizza le notizie e crea un briefing"""
    
    # Prepariamo il testo delle notizie
    testo_notizie = ""
    for i, n in enumerate(notizie, 1):
        testo_notizie += f"""
Notizia {i}: {n['titolo']}
Fonte: {n['fonte']}
Descrizione: {n['descrizione']}
---"""
    
    # Chiediamo a Claude di analizzarle
    messaggio = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Sei un giornalista esperto.
            
Ho trovato queste notizie su "{argomento}":
{testo_notizie}

Per favore:
1. Fai un riassunto delle tendenze principali (3-4 righe)
2. Evidenzia le 2 notizie più importanti e spiega perché
3. Dai un contesto utile per capire meglio il tema

Rispondi in italiano, in modo chiaro e conciso."""
        }]
    )
    
    return messaggio.content[0].text

# Carica le variabili dal file .env


NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def cerca_notizie(argomento, quante=5):
    """Cerca notizie su un argomento"""
    url = "https://newsapi.org/v2/everything"
    
    parametri = {
        "q": argomento,
        "language": "it",
        "sortBy": "publishedAt",
        "pageSize": quante,
        "apiKey": NEWS_API_KEY
    }
    
    risposta = requests.get(url, params=parametri)
    dati = risposta.json()
    
    notizie = []
    for articolo in dati["articles"]:
        notizie.append({
            "titolo": articolo["title"],
            "fonte": articolo["source"]["name"],
            "descrizione": articolo["description"],
            "url": articolo["url"]
        })
    
    return notizie






TOOLS = [
    {
        "name": "cerca_notizie",
        "description": "Cerca le ultime notizie su un argomento specifico",
        "input_schema": {
            "type": "object",
            "properties": {
                "argomento": {
                    "type": "string",
                    "description": "L'argomento da cercare"
                },
                "quante": {
                    "type": "integer",
                    "description": "Numero di notizie (default 5)",
                    "default": 5
                }
            },
            "required": ["argomento"]
        }
    }
]


def agente_notizie(domanda_utente):
    """L'agente decide autonomamente come rispondere"""
    
    messaggi = [{
        "role": "user", 
        "content": domanda_utente
    }]
    
    print("🤖 Agente in esecuzione...\n")
    
    # Loop: continua finché Claude non ha finito
    while True:
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system="""Sei un assistente notizie personale.
Quando l'utente chiede info su un argomento, 
usa il tool cerca_notizie per trovare articoli recenti,
poi analizzali e fornisci un briefing completo in italiano.""",
            tools=TOOLS,
            messages=messaggi
        )
        
        # Claude ha finito? Mostra la risposta
        if risposta.stop_reason == "end_turn":
            for blocco in risposta.content:
                if hasattr(blocco, "text"):
                    print(blocco.text)
            break
        
        # Claude vuole usare un tool?
        if risposta.stop_reason == "tool_use":
            messaggi.append({
                "role": "assistant",
                "content": risposta.content
            })
            
            risultati_tool = []
            for blocco in risposta.content:
                if blocco.type == "tool_use":
                    print(f"🔍 Cerco notizie su: {blocco.input['argomento']}")
                    
                    # Esegui la funzione reale
                    notizie = cerca_notizie(
                        blocco.input["argomento"],
                        blocco.input.get("quante", 5)
                    )
                    
                    risultati_tool.append({
                        "type": "tool_result",
                        "tool_use_id": blocco.id,
                        "content": str(notizie)
                    })
            
            messaggi.append({
                "role": "user",
                "content": risultati_tool
            })


if __name__ == "__main__":
    print("=" * 50)
    print("=" * 50)
    domanda = input("Cosa vuoi sapere? ")
    agente_notizie(domanda)



