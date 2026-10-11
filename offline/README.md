# Offline RAG (Ollama Gemma3)

This folder runs a fully local compliance RAG chatbot using Ollama.

This version is designed to run without internet during usage.

## Offline quality features

- Bundled local official regulation packs in `offline/official_docs`
- Persistent Chroma vector database on disk
- Hybrid retrieval with reranking for stronger relevance
- Advanced controls for retrieval depth and history window

## Prerequisites

```bash
ollama pull gemma3:4b
ollama pull nomic-embed-text
ollama serve
```

## Environment

```bash
copy offline\.env.example .env
```

## Run

```bash
streamlit run offline/app.py
```

## Notes

- Uses local LLM + local embeddings.
- Ingests bundled official EU docs from local files, no web fetch needed.
- Uploaded PDFs are indexed and stored in persistent local vector DB.

## Recommended first run

1. Initialize engine.
2. Let auto-index complete for bundled official docs.
3. Upload your PDFs and click ingest.
4. Ask questions and verify citations.
