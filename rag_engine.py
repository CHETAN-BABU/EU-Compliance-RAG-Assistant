from __future__ import annotations

import os
from typing import List, Tuple

from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from config import OFFICIAL_REGULATION_SOURCES
from llm_factory import build_chat_model, build_embeddings
from web_research import search_regulation_web


class ComplianceRAG:
    def __init__(
        self,
        provider: str,
        chat_model: str,
        embed_model: str,
        temperature: float,
        vector_dir: str,
        ollama_base_url: str,
        gemini_api_key: str = "",
    ) -> None:
        self.provider = provider
        self.vector_dir = vector_dir
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=180)

        self.llm = build_chat_model(
            provider=provider,
            model_name=chat_model,
            temperature=temperature,
            ollama_base_url=ollama_base_url,
            gemini_api_key=gemini_api_key,
        )
        self.embeddings = build_embeddings(
            provider=provider,
            model_name=embed_model,
            ollama_base_url=ollama_base_url,
            gemini_api_key=gemini_api_key,
        )

        self.vectordb = Chroma(
            collection_name="compliance_docs",
            persist_directory=self.vector_dir,
            embedding_function=self.embeddings,
        )

    def _normalize_docs(self, docs: List[Document]) -> List[Document]:
        for d in docs:
            source = d.metadata.get("source", "unknown")
            page = d.metadata.get("page")
            if page is not None:
                d.metadata["citation"] = f"{os.path.basename(source)}#page-{int(page) + 1}"
            else:
                d.metadata["citation"] = str(source)
        return docs

    def ingest_pdfs(self, file_paths: List[str]) -> int:
        docs: List[Document] = []
        for path in file_paths:
            loader = PyPDFLoader(path)
            docs.extend(loader.load())

        docs = self._normalize_docs(docs)
        chunks = self.splitter.split_documents(docs)
        if chunks:
            self.vectordb.add_documents(chunks)
        return len(chunks)

    def ingest_official_sources(self) -> int:
        urls = list(OFFICIAL_REGULATION_SOURCES.values())
        loader = WebBaseLoader(web_paths=urls)
        docs = loader.load()
        docs = self._normalize_docs(docs)
        chunks = self.splitter.split_documents(docs)
        if chunks:
            self.vectordb.add_documents(chunks)
        return len(chunks)

    def answer(
        self,
        question: str,
        chat_history: List[Tuple[str, str]],
        include_live_web: bool = False,
        top_k: int = 6,
    ) -> Tuple[str, List[str]]:
        retriever = self.vectordb.as_retriever(search_type="mmr", search_kwargs={"k": top_k, "fetch_k": 20})
        context_docs = retriever.invoke(question)

        citations = []
        context_blocks = []
        for i, doc in enumerate(context_docs, start=1):
            citation = doc.metadata.get("citation", "unknown")
            citations.append(str(citation))
            context_blocks.append(f"[{i}] Source: {citation}\n{doc.page_content}")

        history_text = "\n".join([f"User: {u}\nAssistant: {a}" for u, a in chat_history[-6:]])
        web_context = ""
        if include_live_web:
            try:
                web_context = search_regulation_web(question)
            except Exception:
                web_context = "Live web enrichment failed for this query. Continue with document-only context."

        prompt = f"""
You are a compliance-focused assistant for EU regulations.

Scope:
- GDPR (EU 2016/679)
- EU AI Act (EU 2024/1689)
- DORA (EU 2022/2554)

Rules:
- Use ONLY the provided context when possible.
- If the context is insufficient, say what is missing.
- Provide practical, structured answers.
- Include a short disclaimer that this is not legal advice.
- Cite sources using [1], [2], etc., tied to provided context.

Conversation history:
{history_text if history_text else 'No prior history'}

Retrieved context:
{chr(10).join(context_blocks) if context_blocks else 'No retrieved documents found.'}

Optional live web snippets:
{web_context if web_context else 'None'}

Question:
{question}
"""

        response = self.llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        return text, sorted(set(citations))
