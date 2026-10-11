# Interview Demo Playbook (Two Separate Apps)

## Goal
Show two distinct applications for the same compliance chatbot task:
- Online app (Azure + optional internet snippets)
- Offline app (fully local Ollama, no internet needed during use)

## App 1: Online Innovation Demo
Run:

```bash
python -m streamlit run online/app.py
```

Narrative:
1. Initialize Azure engine.
2. Ingest official EU docs.
3. Upload a sample PDF policy and ingest it.
4. Use Demo 4 button (cross-regulation gap analysis).
5. Switch Response mode between executive and auditor to show adaptive reporting.
6. Download Last Briefing to show handoff-ready output.

What impresses interviewers:
- Same knowledge base, multiple audience formats (leadership vs audit).
- Regulation focus detection in UI.
- Traceable citations and exportable briefing.

## App 2: Offline Reliability Demo
Run:

```bash
python -m streamlit run offline/app.py
```

Narrative:
1. Explain this app works without internet during usage.
2. Initialize offline engine and show auto-index of local official packs.
3. Show vector chunk count and persistent store behavior.
4. Use Demo 3 button (DORA third-party audit).
5. Show Clear Vector DB and re-ingest behavior for controlled testing.
6. Download Last Briefing to show offline report generation.

What impresses interviewers:
- Air-gapped friendly design.
- Persistent local vector DB.
- Hybrid retrieval + reranking for quality without cloud retrieval.

## Suggested Interview One-Liner
"I solved the same compliance QA task in two production styles: cloud-augmented and air-gapped offline, each with citation-backed RAG, audience-specific reporting modes, and demo scenarios tailored for real audit and executive workflows."
