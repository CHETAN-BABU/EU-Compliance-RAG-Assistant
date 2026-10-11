from __future__ import annotations

import os
from pathlib import Path
import uuid

import streamlit as st
from dotenv import load_dotenv

from config import OFFICIAL_REGULATION_SOURCES, get_settings
from rag_engine import OfflineComplianceRAG

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(Path(__file__).with_name(".env"))

st.set_page_config(page_title="Offline Compliance Assistant", page_icon="OF", layout="wide")
st.title("Offline Compliance Assistant")
st.caption("Simple ChatGPT-style compliance chatbot running fully local with Ollama + RAG.")

if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = [
        {"id": f"chat-{uuid.uuid4().hex[:8]}", "title": "New Chat", "messages": [], "chat_history": []}
    ]
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = st.session_state.chat_sessions[0]["id"]


def build_chat_title(user_text: str) -> str:
    cleaned = " ".join(user_text.strip().split())
    if not cleaned:
        return "New Chat"
    return f"{cleaned[:42]}..." if len(cleaned) > 42 else cleaned


def get_active_chat() -> dict:
    active_id = st.session_state.active_chat_id
    for chat in st.session_state.chat_sessions:
        if chat["id"] == active_id:
            return chat
    fallback = st.session_state.chat_sessions[0]
    st.session_state.active_chat_id = fallback["id"]
    return fallback


def start_new_chat() -> None:
    new_chat = {"id": f"chat-{uuid.uuid4().hex[:8]}", "title": "New Chat", "messages": [], "chat_history": []}
    st.session_state.chat_sessions.insert(0, new_chat)
    st.session_state.active_chat_id = new_chat["id"]

settings = get_settings()

with st.sidebar:
    st.subheader("Chats")
    if st.button("+ New Chat", use_container_width=True):
        start_new_chat()
        st.rerun()

    for chat in st.session_state.chat_sessions:
        is_active = chat["id"] == st.session_state.active_chat_id
        label = f"● {chat['title']}" if is_active else chat["title"]
        if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
            st.session_state.active_chat_id = chat["id"]
            st.rerun()

    active_chat = get_active_chat()
    if st.button("Clear Current Chat", use_container_width=True):
        active_chat["messages"] = []
        active_chat["chat_history"] = []
        active_chat["title"] = "New Chat"
        st.rerun()

    st.divider()
    with st.expander("Engine Settings", expanded=False):
        base_url = st.text_input("OLLAMA_BASE_URL", value=settings.ollama_base_url)
        chat_model = st.text_input("OLLAMA_CHAT_MODEL", value=settings.ollama_chat_model)
        embed_model = st.text_input("OLLAMA_EMBED_MODEL", value=settings.ollama_embed_model)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)

    vector_dir = settings.vector_db_dir
    upload_dir = settings.upload_dir
    official_docs_dir = settings.official_docs_dir
    Path(vector_dir).mkdir(parents=True, exist_ok=True)
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    Path(official_docs_dir).mkdir(parents=True, exist_ok=True)

    top_k = 7
    max_history_turns = 8
    detail_level = "detailed"
    response_style = "standard"
    enable_eval = False

    if st.button("Initialize Engine", use_container_width=True):
        try:
            st.session_state.rag_engine = OfflineComplianceRAG(
                base_url=base_url,
                chat_model=chat_model,
                embed_model=embed_model,
                vector_dir=vector_dir,
                official_docs_dir=official_docs_dir,
                temperature=temperature,
            )
            st.success("Offline engine initialized.")
        except Exception as exc:
            st.error(f"Initialization failed: {exc}")

    if st.session_state.rag_engine is not None:
        st.caption(f"Vector chunks stored: {st.session_state.rag_engine.vector_count()}")

    with st.expander("Knowledge Base", expanded=False):
        uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

        if st.button("Ingest Uploaded PDFs", use_container_width=True):
            if st.session_state.rag_engine is None:
                st.error("Initialize engine first.")
            elif not uploaded_files:
                st.warning("Upload PDFs first.")
            else:
                paths = []
                for f in uploaded_files:
                    p = os.path.join(upload_dir, f.name)
                    with open(p, "wb") as out:
                        out.write(f.getbuffer())
                    paths.append(p)
                chunks = st.session_state.rag_engine.ingest_pdfs(paths)
                st.success(f"Indexed {chunks} chunks from PDFs.")

        if st.button("Ingest Official EU Docs", use_container_width=True):
            if st.session_state.rag_engine is None:
                st.error("Initialize engine first.")
            else:
                chunks = st.session_state.rag_engine.ingest_official_sources()
                st.success(f"Indexed {chunks} chunks from official docs.")

        if st.button("Clear Vector DB", use_container_width=True):
            if st.session_state.rag_engine is None:
                st.error("Initialize engine first.")
            else:
                st.session_state.rag_engine.clear_vector_store()
                st.success("Vector DB cleared.")

    with st.expander("Bundled Official Packs", expanded=False):
        for name, meta in OFFICIAL_REGULATION_SOURCES.items():
            st.write(f"- {name}: {meta.get('local_file', '')}")

active_chat = get_active_chat()

for message in active_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Ask a compliance question...")

if query:
    if active_chat["title"] == "New Chat":
        active_chat["title"] = build_chat_title(query)

    active_chat["messages"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    answer = ""
    with st.chat_message("assistant"):
        if st.session_state.rag_engine is None:
            answer = "Initialize the offline engine from sidebar first."
            st.markdown(answer)
        else:
            try:
                answer, citations, metadata = st.session_state.rag_engine.answer(
                    question=query,
                    chat_history=active_chat["chat_history"],
                    top_k=top_k,
                    max_history_turns=max_history_turns,
                    detail_level=detail_level,
                    response_style=response_style,
                    enable_self_eval=enable_eval,
                )
                st.markdown(answer)
            except Exception as exc:
                answer = f"I hit an error while generating the answer: {exc}"
                citations = []
                st.error(answer)

            if citations:
                with st.expander("Sources", expanded=False):
                    for c in citations:
                        st.markdown(f"- {c}")

    active_chat["messages"].append({"role": "assistant", "content": answer})
    active_chat["chat_history"].append((query, answer))
