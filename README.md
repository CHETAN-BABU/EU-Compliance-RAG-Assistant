# EU Compliance RAG Chatbot Suite

A from-scratch RAG chatbot for:
- GDPR (EU 2016/679)
- EU AI Act (EU 2024/1689)
- DORA (EU 2022/2554)

This workspace now contains three runnable apps:
- `app.py`: mixed provider app (Ollama or Gemini)
- `online/app.py`: Azure OpenAI focused app
- `offline/app.py`: fully local Ollama Gemma app

Both `online` and `offline` include:
- PDF upload and indexing
- Official EUR-Lex source ingestion (GDPR, EU AI Act, DORA)
- Source-cited RAG chat answers

## Why this build is better

- Uses official EUR-Lex regulation pages as optional grounding.
- Keeps your local workflow with Ollama, but can switch to Gemini instantly.
- Uses retrieval + citations instead of pure chat guessing.
- Supports your own compliance PDFs (policies, controls, legal guidance).

## Official source links

- GDPR: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- EU AI Act: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- DORA: https://eur-lex.europa.eu/eli/reg/2022/2554/oj

## 1) Install

```bash
cd compliance-rag-assistant
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Ollama setup (local)

```bash
ollama pull gemma3:4b
ollama pull nomic-embed-text
ollama serve
```

## 3) Configure env

```bash
copy .env.example .env
```

Set values in `.env` for the root app if you run `app.py`.

For the separate online/offline apps, see:
- `online/.env.example`
- `offline/.env.example`

## 4) Run apps

```bash
streamlit run app.py
streamlit run online/app.py
streamlit run offline/app.py
```

## How to use

1. Start one app.
2. Initialize engine from sidebar.
3. Upload PDF files and click ingest.
4. Click ingest for official EU sources.
5. Ask questions in chat.

## Notes

- This tool is for informational support, not legal advice.
- For legal decisions, consult a qualified legal professional.
