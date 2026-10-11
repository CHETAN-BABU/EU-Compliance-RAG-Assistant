# Online RAG (Azure OpenAI)

This folder runs a compliance RAG chatbot using Azure OpenAI for chat generation.

Features:
- Official docs ingestion for GDPR, EU AI Act, DORA (EUR-Lex)
- PDF upload and RAG over your uploaded documents
- Advanced retrieval modes: MMR, similarity, score-threshold
- Adjustable Top-K and chat history window
- Optional live internet snippets for fresher context
- Strict grounding mode to reduce hallucinations

## Environment

Copy this file first:

```bash
copy online\.env.example .env
```

Fill in your key in `.env`.

## Run

```bash
streamlit run online/app.py
```

## Quick verification checklist

1. Initialize engine from sidebar (Azure fields set).
2. Ingest official docs.
3. Upload at least one PDF and ingest.
4. Ask one question about regulation text and one from PDF content.
5. Confirm citations appear under response.

## Notes

- Official docs ingestion button pulls GDPR, EU AI Act, and DORA from EUR-Lex.
- If `AZURE_EMBEDDING_DEPLOYMENT` is empty, local HF embeddings are used.
