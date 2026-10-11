from __future__ import annotations

from duckduckgo_search import DDGS


def search_regulation_web(query: str, max_results: int = 4) -> str:
    """Fetch short web snippets to enrich answers with recent context."""
    search_query = (
        f"{query} (GDPR OR 'EU AI Act' OR DORA regulation) site:europa.eu OR site:eur-lex.europa.eu"
    )

    snippets = []
    with DDGS() as ddgs:
        for idx, result in enumerate(ddgs.text(search_query, max_results=max_results), start=1):
            title = result.get("title", "No title")
            href = result.get("href", "")
            body = result.get("body", "")
            snippets.append(f"{idx}. {title}\nURL: {href}\nSnippet: {body}")

    return "\n\n".join(snippets)
