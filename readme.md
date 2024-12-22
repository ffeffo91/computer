# Smart Assistant

## Descrizione
Smart Assistant è un prototipo di assistente vocale (tipo Google Home o Alexa) costruito con le moderne tecniche di Agentic AI.
L'agente è stato costruito con la libreria Langgraph, il grafo che ne descrive il flusso è mostrato nella seguente immagine:
![graph](graph.png "Grafo che descrive il flusso dell'agente")

## Modelli
Il progetto comprende l'integrazione di diversi modelli di AI:
1. VAD ([Voice Activity Detector](https://github.com/snakers4/silero-vad)):
Questo modello permette di individuare l'attività vocale, è fondamentale per capire quando l'utente ha iniziato a parlare.
2. STT ([Speech To Text](https://github.com/SYSTRAN/faster-whisper)):
Per tradurre in testo la voce registrata.
3. TTS ([Text To Speech](https://pypi.org/project/pyttsx3/)):
Per tradurre in audio la risposta dell'LLM.
4. LLM ([Large Language Model](https://platform.openai.com/docs/api-reference/introduction)):
E' l'intelligenza artificiale in grado di utilizzare i tool a disposizione per risolvere le richieste dell'utente.

## Inizializzazione
1. crea un ambiente python e installa le dipendenze con il comando
```bash
pip install -r requirements.txt
```
2. crea un file .env con il seguente contenuto
```
OPENAI_API_KEY="openai-key"
TAVILY_API_KEY="tavily-key"
```