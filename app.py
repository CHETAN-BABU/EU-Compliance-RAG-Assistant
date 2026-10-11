from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from config import OFFICIAL_REGULATION_SOURCES, get_settings
from rag_engine import ComplianceRAG

load_dotenv()

st.set_page_config(page_title="EU Compliance RAG Chat", page_icon="EU", layout="wide")
st.title("EU Compliance RAG Chatbot")
st.caption("Ask about GDPR, EU AI Act, and DORA with local or cloud LLMs.")


if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None
if "engine_signature" not in st.session_state:
    st.session_state.engine_signature = None


settings = get_settings()

with st.sidebar:
    st.header("Model Settings")
    provider = st.selectbox("Provider", ["ollama", "gemini"], index=0 if settings.llm_provider == "ollama" else 1)

    if provider == "ollama":
        chat_model = st.text_input("Ollama chat model", value=settings.ollama_chat_model)
        embed_model = st.text_input("Ollama embedding model", value=settings.ollama_embed_model)
        gemini_api_key = ""
    else:
        chat_model = st.text_input("Gemini chat model", value=settings.gemini_chat_model)
        embed_model = st.text_input("Gemini embedding model", value=settings.gemini_embed_model)
        gemini_api_key = st.text_input("Gemini API key", value=settings.gemini_api_key, type="password")

    ollama_base_url = st.text_input("Ollama base URL", value=settings.ollama_base_url)
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
    use_live_web = st.toggle("Use live web snippets", value=True)

    st.divider()
    st.subheader("Knowledge Base")
    uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

    vector_dir = settings.vector_db_dir
    upload_dir = settings.upload_dir
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    Path(vector_dir).mkdir(parents=True, exist_ok=True)

    engine_signature = f"{provider}|{chat_model}|{embed_model}|{temperature}|{ollama_base_url}"

    if st.session_state.rag_engine is None or st.session_state.engine_signature != engine_signature:
        st.session_state.rag_engine = ComplianceRAG(
            provider=provider,
            chat_model=chat_model,
            embed_model=embed_model,
            temperature=temperature,
            vector_dir=vector_dir,
            ollama_base_url=ollama_base_url,
            gemini_api_key=gemini_api_key,
        )
        st.session_state.engine_signature = engine_signature

    if st.button("Ingest Uploaded PDFs", use_container_width=True):
        if not uploaded_files:
            st.warning("Upload at least one PDF first.")
        else:
            saved_paths = []
            for f in uploaded_files:
                out_path = os.path.join(upload_dir, f.name)
                with open(out_path, "wb") as handle:
                    handle.write(f.getbuffer())
                saved_paths.append(out_path)

            with st.spinner("Indexing PDF documents..."):
                chunks = st.session_state.rag_engine.ingest_pdfs(saved_paths)
            st.success(f"Indexed {chunks} chunks from PDF documents.")

    if st.button("Ingest Official EU Sources", use_container_width=True):
        with st.spinner("Fetching and indexing official regulation sources..."):
            chunks = st.session_state.rag_engine.ingest_official_sources()
        st.success(f"Indexed {chunks} chunks from official web sources.")

    st.caption("Official source URLs")
    for name, url in OFFICIAL_REGULATION_SOURCES.items():
        st.write(f"- {name}: {url}")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_query = st.chat_input("Ask about GDPR, EU AI Act, DORA, obligations, penalties, scope, controls...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking with retrieved regulation context..."):
            answer, citations = st.session_state.rag_engine.answer(
                question=user_query,
                chat_history=st.session_state.chat_history,
                include_live_web=use_live_web,
            )

            st.markdown(answer)
            if citations:
                st.markdown("**Sources used**")
                for c in citations:
                    st.markdown(f"- {c}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.chat_history.append((user_query, answer))
