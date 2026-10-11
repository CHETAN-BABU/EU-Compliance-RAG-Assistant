from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    ollama_chat_model: str
    ollama_embed_model: str
    vector_db_dir: str
    upload_dir: str
    official_docs_dir: str


OFFICIAL_REGULATION_SOURCES = {
    "GDPR": {
        "official_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "local_file": "gdpr_official_pack.md",
    },
    "EU AI Act": {
        "official_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        "local_file": "eu_ai_act_official_pack.md",
    },
    "DORA": {
        "official_url": "https://eur-lex.europa.eu/eli/reg/2022/2554/oj",
        "local_file": "dora_official_pack.md",
    },
}


def get_settings() -> Settings:
    return Settings(
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip(),
        ollama_chat_model=os.getenv("OLLAMA_CHAT_MODEL", "gemma3:4b").strip(),
        ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text").strip(),
        vector_db_dir=os.getenv("VECTOR_DB_DIR", "offline/.chroma_db").strip(),
        upload_dir=os.getenv("UPLOAD_DIR", "offline/uploaded_docs").strip(),
        official_docs_dir=os.getenv("OFFICIAL_DOCS_DIR", "offline/official_docs").strip(),
    )
