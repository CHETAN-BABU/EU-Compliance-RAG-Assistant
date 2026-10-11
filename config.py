from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    ollama_chat_model: str
    ollama_embed_model: str
    ollama_base_url: str
    gemini_api_key: str
    gemini_chat_model: str
    gemini_embed_model: str
    vector_db_dir: str
    upload_dir: str


OFFICIAL_REGULATION_SOURCES = {
    "GDPR": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    "EU AI Act": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "DORA": "https://eur-lex.europa.eu/eli/reg/2022/2554/oj",
}


def get_settings() -> Settings:
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "ollama").strip().lower(),
        ollama_chat_model=os.getenv("OLLAMA_CHAT_MODEL", "gemma3:4b").strip(),
        ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text").strip(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_chat_model=os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash").strip(),
        gemini_embed_model=os.getenv("GEMINI_EMBED_MODEL", "models/text-embedding-004").strip(),
        vector_db_dir=os.getenv("VECTOR_DB_DIR", ".chroma_db").strip(),
        upload_dir=os.getenv("UPLOAD_DIR", "uploaded_docs").strip(),
    )
