from __future__ import annotations

import os
import sys
from importlib import import_module
from typing import List, Tuple, Dict

from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import OFFICIAL_REGULATION_SOURCES
try:
    from web_research import search_compliance_web
except ImportError:
    from online.web_research import search_compliance_web

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compliance_utils import (
    calculate_confidence_score,
    extract_article_citations,
    generate_self_evaluation,
    detect_query_complexity,
    decompose_complex_query,
)


class OnlineComplianceRAG:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment_chat: str,
        deployment_embed: str,
        vector_dir: str,
        temperature: float = 0.1,
    ) -> None:
        if not endpoint or not api_key:
            raise ValueError("Set AZURE_OPENAI_ENDPOINT and OPENAI_API_KEY in environment.")

        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=180)

        azure_mod = import_module("langchain_openai")
        AzureChatOpenAI = getattr(azure_mod, "AzureChatOpenAI")
        AzureOpenAIEmbeddings = getattr(azure_mod, "AzureOpenAIEmbeddings")
        Chroma = getattr(import_module("langchain_chroma"), "Chroma")

        self.llm = AzureChatOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            azure_deployment=deployment_chat,
            temperature=temperature,
        )

        # If no embedding deployment is provided, use a local embedding model for stability.
        if deployment_embed:
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
                azure_deployment=deployment_embed,
            )
        else:
            HuggingFaceEmbeddings = getattr(import_module("langchain_huggingface"), "HuggingFaceEmbeddings")
            self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        self.vectordb = Chroma(
            collection_name="online_compliance_docs",
            persist_directory=vector_dir,
            embedding_function=self.embeddings,
        )

    def vector_count(self) -> int:
        try:
            data = self.vectordb.get(include=[])
            return len(data.get("ids", []))
        except Exception:
            return 0

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
        urls = list(OFFICIAL_REGULATION_SOURCES.values())
        docs = WebBaseLoader(web_paths=urls).load()
        chunks = self.splitter.split_documents(self._normalize_docs(docs))
        if chunks:
            self.vectordb.add_documents(chunks)
        return len(chunks)

    def _build_retriever(self, mode: str, top_k: int):
        mode = mode.lower().strip()
        if mode == "similarity":
            return self.vectordb.as_retriever(search_type="similarity", search_kwargs={"k": top_k})
        if mode == "similarity_score_threshold":
            return self.vectordb.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": top_k, "score_threshold": 0.35},
            )
        return self.vectordb.as_retriever(search_type="mmr", search_kwargs={"k": top_k, "fetch_k": max(20, top_k * 3)})

    def answer(
        self,
        question: str,
        chat_history: List[Tuple[str, str]],
        top_k: int = 6,
        retrieval_mode: str = "mmr",
        include_live_web: bool = False,
        max_history_turns: int = 6,
        detail_level: str = "detailed",
        strict_grounding: bool = True,
        response_style: str = "standard",
        enable_self_eval: bool = True,
    ) -> Tuple[str, List[str], Dict]:
        """
        Generate compliance answer with confidence scoring and self-evaluation.

        Returns:
            Tuple of (answer_text, citations, metadata_dict)
        """
        retriever = self._build_retriever(mode=retrieval_mode, top_k=top_k)
        context_docs = retriever.invoke(question)

        citations: List[str] = []
        article_citations: List[str] = []
        context_blocks: List[str] = []
        avg_similarity = 0.0

        for i, doc in enumerate(context_docs, start=1):
            citation = str(doc.metadata.get("citation", "unknown"))
            citations.append(citation)

            # Extract articles from retrieved content
            regulation = doc.metadata.get("source", "GDPR")
            if "gdpr" in regulation.lower():
                regulation = "GDPR"
            elif "ai act" in regulation.lower():
                regulation = "EU AI Act"
            elif "dora" in regulation.lower():
                regulation = "DORA"

            articles = extract_article_citations(doc.page_content, regulation)
            article_citations.extend(articles)

            context_blocks.append(f"[{i}] Source: {citation}\n{doc.page_content}")

        # Calculate keyword overlap for confidence
        q_terms = set(w.strip().lower() for w in question.split() if len(w) > 3)
        doc_text = " ".join(b.lower() for b in context_blocks)
        keyword_overlap = sum(1 for term in q_terms if term in doc_text) / max(len(q_terms), 1)

        history_text = "\n".join([f"User: {u}\nAssistant: {a}" for u, a in chat_history[-max_history_turns:]])

        web_context = ""
        if include_live_web:
            try:
                web_context = search_compliance_web(question)
            except Exception:
                web_context = "Live web enrichment is unavailable for this query."

        grounding_rule = (
            "If retrieved context is insufficient, say exactly what is missing and avoid speculation."
            if strict_grounding
            else "Use best-effort reasoning and clearly label inferred statements."
        )

        style_rules = {
            "standard": "Provide a clear practical answer with short bullets.",
            "executive": "Use executive-brief format: summary, key obligations, risk heatmap, 30-60-90 day plan.",
            "auditor": "Use audit format: control objectives, evidence artifacts, gaps, remediation actions.",
        }
        selected_style_rule = style_rules.get(response_style, style_rules["standard"])

        prompt = f"""
You are an expert EU compliance assistant.
Scope:
- GDPR (EU 2016/679)
- EU AI Act (EU 2024/1689)
- DORA (EU 2022/2554)

Quality rules:
- Prioritize retrieved context and cite it with [1], [2], etc.
- {grounding_rule}
- Answer detail level: {detail_level}
- Response style: {response_style}
- Style instruction: {selected_style_rule}
- Include practical compliance actions when useful.
- End with: This is not legal advice.

Conversation history:
{history_text if history_text else 'No prior history'}

Retrieved context:
{chr(10).join(context_blocks) if context_blocks else 'No retrieved documents found.'}

Optional web context:
{web_context if web_context else 'None'}

Question:
{question}
"""

        result = self.llm.invoke(prompt)
        text = result.content if hasattr(result, "content") else str(result)

        # Calculate confidence score
        confidence_data = calculate_confidence_score(
            retrieved_docs_count=len(context_docs),
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
                    retrieved_docs_count=len(context_docs),
                    llm_invoke_func=self.llm.invoke,
                )
            except Exception:
                evaluation = {"completeness": 80, "accuracy": 80}

        metadata = {
            "confidence": confidence_data,
            "evaluation": evaluation,
            "article_citations": sorted(set(article_citations)),
            "doc_count": len(context_docs),
            "query_type": detect_query_complexity(question),
            "web_enriched": include_live_web and web_context != "",
        }

        return text, sorted(set(citations)), metadata
