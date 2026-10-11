from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))


@dataclass(frozen=True)
class Settings:
    azure_openai_endpoint: str
    openai_api_key: str
    azure_openai_api_version: str
    azure_deployment_principal: str
    azure_deployment_child: str
    azure_embedding_deployment: str
    vector_db_dir: str
    upload_dir: str


OFFICIAL_REGULATION_SOURCES = {
    "GDPR": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    "EU AI Act": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "DORA": "https://eur-lex.europa.eu/eli/reg/2022/2554/oj",
}


def get_settings() -> Settings:
    return Settings(
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview").strip(),
        azure_deployment_principal=os.getenv("AZURE_DEPLOYMENT_PRINCIPAL", "gpt-4.1").strip(),
        azure_deployment_child=os.getenv("AZURE_DEPLOYMENT_CHILD", "gpt-4.1").strip(),
        azure_embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "").strip(),
        vector_db_dir=os.getenv("VECTOR_DB_DIR", "online/.chroma_db").strip(),
        upload_dir=os.getenv("UPLOAD_DIR", "online/uploaded_docs").strip(),
    )
