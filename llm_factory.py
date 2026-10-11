from __future__ import annotations

from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings


def build_chat_model(
    provider: str,
    model_name: str,
    temperature: float,
    ollama_base_url: str,
    gemini_api_key: Optional[str] = None,
):
    provider = provider.lower().strip()

    if provider == "ollama":
        return ChatOllama(
            model=model_name,
            base_url=ollama_base_url,
            temperature=temperature,
        )

    if provider == "gemini":
        if not gemini_api_key:
            raise ValueError("Gemini API key is missing. Set GEMINI_API_KEY in .env.")
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=gemini_api_key,
        )

    raise ValueError(f"Unsupported provider: {provider}")


def build_embeddings(
    provider: str,
    model_name: str,
    ollama_base_url: str,
    gemini_api_key: Optional[str] = None,
):
    provider = provider.lower().strip()

    if provider == "ollama":
        return OllamaEmbeddings(model=model_name, base_url=ollama_base_url)

    if provider == "gemini":
        if not gemini_api_key:
            raise ValueError("Gemini API key is missing. Set GEMINI_API_KEY in .env.")
        return GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=gemini_api_key,
        )

    # Safe fallback if provider value is unexpected.
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
