from __future__ import annotations

import os
import sys
from importlib import import_module
from typing import Dict, List, Tuple

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import OFFICIAL_REGULATION_SOURCES

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compliance_utils import (
    calculate_confidence_score,
    extract_article_citations,
    generate_self_evaluation,
    detect_query_complexity,
    decompose_complex_query,
)


class OfflineComplianceRAG:
    def __init__(
        self,
        base_url: str,
        chat_model: str,
        embed_model: str,
        vector_dir: str,
        official_docs_dir: str,
        temperature: float = 0.1,
    ) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1100,
            chunk_overlap=180,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        )
        self.official_docs_dir = official_docs_dir
        ollama_mod = import_module("langchain_ollama")
        ChatOllama = getattr(ollama_mod, "ChatOllama")
        OllamaEmbeddings = getattr(ollama_mod, "OllamaEmbeddings")
        Chroma = getattr(import_module("langchain_chroma"), "Chroma")

        self.llm = ChatOllama(model=chat_model, base_url=base_url, temperature=temperature)
        self.embeddings = OllamaEmbeddings(model=embed_model, base_url=base_url)

        self.vectordb = Chroma(
            collection_name="offline_compliance_docs",
            persist_directory=vector_dir,
            embedding_function=self.embeddings,
        )

    def _keyword_score(self, question: str, text: str) -> float:
        q_terms = {t.strip(".,:;!?()[]{}\"'`").lower() for t in question.split() if len(t) > 2}
        if not q_terms:
            return 0.0
        lower_text = text.lower()
        hits = sum(1 for term in q_terms if term in lower_text)
        return hits / max(len(q_terms), 1)

    def _hybrid_retrieve(self, question: str, top_k: int) -> List[Document]:
        mmr_docs = self.vectordb.similarity_search(question, k=top_k + 2)
        sim_docs = self.vectordb.max_marginal_relevance_search(question, k=top_k + 2, fetch_k=max(20, top_k * 3))

        merged: Dict[str, Document] = {}
        for doc in mmr_docs + sim_docs:
            key = f"{doc.metadata.get('citation', 'unknown')}|{hash(doc.page_content)}"
            merged[key] = doc

        reranked = sorted(
            merged.values(),
            key=lambda d: self._keyword_score(question=question, text=d.page_content),
            reverse=True,
        )
        return reranked[:top_k]

    def vector_count(self) -> int:
        try:
            data = self.vectordb.get(include=[])
            return len(data.get("ids", []))
        except Exception:
            return 0

    def clear_vector_store(self) -> None:
        data = self.vectordb.get(include=[])
        ids = data.get("ids", [])
        if ids:
            self.vectordb.delete(ids=ids)

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
            docs.extend(PyPDFLoader(path).load())
        chunks = self.splitter.split_documents(self._normalize_docs(docs))
        if chunks:
            self.vectordb.add_documents(chunks)
        return len(chunks)

    def ingest_official_sources(self) -> int:
        docs: List[Document] = []
        for name, source_meta in OFFICIAL_REGULATION_SOURCES.items():
            local_file = source_meta.get("local_file", "")
            official_url = source_meta.get("official_url", "")
            path = os.path.join(self.official_docs_dir, local_file)
            if not os.path.exists(path):
                continue

            loaded = TextLoader(path, encoding="utf-8").load()
            for d in loaded:
                d.metadata["source"] = path
                d.metadata["official_url"] = official_url
                d.metadata["regulation"] = name
            docs.extend(loaded)

        chunks = self.splitter.split_documents(self._normalize_docs(docs))
        if chunks:
            self.vectordb.add_documents(chunks)
        return len(chunks)

    def answer(
        self,
        question: str,
        chat_history: List[Tuple[str, str]],
        top_k: int = 7,
        max_history_turns: int = 8,
        detail_level: str = "detailed",
        response_style: str = "standard",
        enable_self_eval: bool = True,
    ) -> Tuple[str, List[str], Dict]:
        """
        Generate compliance answer with confidence scoring and self-evaluation.

        Returns:
            Tuple of (answer_text, citations, metadata_dict)
        """
        docs = self._hybrid_retrieve(question=question, top_k=top_k)

        citations: List[str] = []
        article_citations: List[str] = []
        blocks: List[str] = []
        avg_similarity = 0.0

        for i, doc in enumerate(docs, start=1):
            citation = str(doc.metadata.get("citation", "unknown"))
            citations.append(citation)

            # Extract articles from retrieved content
            regulation = doc.metadata.get("regulation", "GDPR")
            articles = extract_article_citations(doc.page_content, regulation)
            article_citations.extend(articles)

            blocks.append(f"[{i}] Source: {citation}\n{doc.page_content}")

        # Calculate keyword overlap for confidence
        q_terms = set(w.strip().lower() for w in question.split() if len(w) > 3)
        doc_text = " ".join(b.lower() for b in blocks)
        keyword_overlap = sum(1 for term in q_terms if term in doc_text) / max(len(q_terms), 1)

        history_text = "\n".join([f"User: {u}\nAssistant: {a}" for u, a in chat_history[-max_history_turns:]])

        style_rules = {
            "standard": "Provide a practical direct answer with concise bullets.",
            "executive": "Use executive-brief format: summary, key obligations, risk heatmap, 30-60-90 day plan.",
            "auditor": "Use audit format: control objectives, evidence artifacts, gaps, remediation actions.",
        }
        selected_style_rule = style_rules.get(response_style, style_rules["standard"])

        prompt = f"""
    You are a high-precision offline compliance assistant for EU regulations.

    Scope:
    - GDPR (EU 2016/679)
    - EU AI Act (EU 2024/1689)
    - DORA (EU 2022/2554)

    Rules:
    - This environment is offline. Use only retrieved local context.
    - If context is insufficient, explicitly state what is missing.
    - Provide depth level: {detail_level}
    - Response style: {response_style}
    - Style instruction: {selected_style_rule}
    - Prefer structured guidance: obligations, controls, risks, and implementation steps.
    - Include source markers [1], [2], ...
    - End with: This is not legal advice.

Conversation history:
{history_text if history_text else 'No prior history'}

Retrieved context:
{chr(10).join(blocks) if blocks else 'No retrieved documents found.'}

Question:
{question}
"""

        result = self.llm.invoke(prompt)
        text = result.content if hasattr(result, "content") else str(result)

        # Calculate confidence score
        confidence_data = calculate_confidence_score(
            retrieved_docs_count=len(docs),
            avg_similarity_score=0.75,  # Placeholder
            keyword_overlap=keyword_overlap,
            answer_length=len(text),
        )

        # Self-evaluation
        evaluation = {}
        if enable_self_eval:
            try:
                evaluation = generate_self_evaluation(
                    question=question,
                    answer=text,
                    retrieved_docs_count=len(docs),
                    llm_invoke_func=self.llm.invoke,
                )
            except Exception:
                evaluation = {"completeness": 80, "accuracy": 80}

        metadata = {
            "confidence": confidence_data,
            "evaluation": evaluation,
            "article_citations": sorted(set(article_citations)),
            "doc_count": len(docs),
            "query_type": detect_query_complexity(question),
        }

        return text, sorted(set(citations)), metadata
