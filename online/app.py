from __future__ import annotations

import os
from pathlib import Path
import sys
import uuid

import streamlit as st
from dotenv import load_dotenv

from config import OFFICIAL_REGULATION_SOURCES, get_settings
from rag_engine import OnlineComplianceRAG

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(Path(__file__).with_name(".env"))

st.set_page_config(page_title="Online Compliance Assistant", page_icon="AZ", layout="wide")
st.title("Online Compliance Assistant")
st.caption("Simple ChatGPT-style compliance chatbot powered by Azure OpenAI + RAG.")

if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None
if "online_engine_error" not in st.session_state:
    st.session_state.online_engine_error = ""
if "online_docs_seeded" not in st.session_state:
    st.session_state.online_docs_seeded = False
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

endpoint = st.session_state.get("online_endpoint", settings.azure_openai_endpoint)
api_key = st.session_state.get("online_api_key", settings.openai_api_key)
api_version = st.session_state.get("online_api_version", settings.azure_openai_api_version)
deployment_chat = st.session_state.get("online_deployment_chat", settings.azure_deployment_principal)
deployment_child = st.session_state.get("online_deployment_child", settings.azure_deployment_child)
deployment_embed = st.session_state.get("online_deployment_embed", settings.azure_embedding_deployment)
temperature = st.session_state.get("online_temperature", 0.1)

vector_dir = settings.vector_db_dir
upload_dir = settings.upload_dir
Path(vector_dir).mkdir(parents=True, exist_ok=True)
Path(upload_dir).mkdir(parents=True, exist_ok=True)

if st.session_state.rag_engine is None:
    try:
        st.session_state.rag_engine = OnlineComplianceRAG(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment_chat=deployment_chat,
            deployment_embed=deployment_embed,
            vector_dir=vector_dir,
            temperature=temperature,
        )
        st.session_state.online_engine_error = ""
    except Exception as exc:
        st.session_state.online_engine_error = str(exc)

if st.session_state.rag_engine is not None and not st.session_state.online_docs_seeded:
    try:
        if st.session_state.rag_engine.vector_count() == 0:
            st.session_state.rag_engine.ingest_official_sources()
        st.session_state.online_docs_seeded = True
    except Exception:
        st.session_state.online_docs_seeded = False

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
        endpoint = st.text_input("AZURE_OPENAI_ENDPOINT", value=endpoint, key="online_endpoint")
        api_key = st.text_input("OPENAI_API_KEY", value=api_key, type="password", key="online_api_key")
        api_version = st.text_input("AZURE_OPENAI_API_VERSION", value=api_version, key="online_api_version")
        deployment_chat = st.text_input("AZURE_DEPLOYMENT_PRINCIPAL", value=deployment_chat, key="online_deployment_chat")
        deployment_child = st.text_input("AZURE_DEPLOYMENT_CHILD", value=deployment_child, key="online_deployment_child")
        deployment_embed = st.text_input("AZURE_EMBEDDING_DEPLOYMENT", value=deployment_embed, key="online_deployment_embed")
        temperature = st.slider("Temperature", 0.0, 1.0, temperature, 0.05, key="online_temperature")

        if st.button("Reconnect Engine", use_container_width=True):
            st.session_state.rag_engine = None
            st.session_state.online_docs_seeded = False
            st.rerun()

    top_k = 6
    retrieval_mode = "mmr"
    max_history_turns = 6
    detail_level = "detailed"
    response_style = "standard"
    include_live_web = True
    strict_grounding = True
    enable_eval = False

    if st.session_state.rag_engine is not None:
        st.caption("Engine ready")
    elif st.session_state.online_engine_error:
        st.error(f"Engine auto-initialization failed: {st.session_state.online_engine_error}")

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

    if st.session_state.rag_engine is not None:
        st.caption(f"Vector chunks stored: {st.session_state.rag_engine.vector_count()}")

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
            answer = "Engine is not available. Check Engine Settings and click Reconnect Engine."
            st.markdown(answer)
        else:
            try:
                answer, citations, metadata = st.session_state.rag_engine.answer(
                    question=query,
                    chat_history=active_chat["chat_history"],
                    top_k=top_k,
                    retrieval_mode=retrieval_mode,
                    include_live_web=include_live_web,
                    max_history_turns=max_history_turns,
                    detail_level=detail_level,
                    strict_grounding=strict_grounding,
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
