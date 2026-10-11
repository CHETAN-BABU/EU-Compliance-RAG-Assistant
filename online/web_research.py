from __future__ import annotations

from duckduckgo_search import DDGS


def search_compliance_web(query: str, max_results: int = 5) -> str:
    """Return short web snippets focused on official EU legal sources."""
    refined_query = (
        f"{query} (GDPR OR \"EU AI Act\" OR DORA regulation) site:eur-lex.europa.eu OR site:europa.eu"
    )

    snippets = []
    with DDGS() as ddgs:
        for idx, result in enumerate(ddgs.text(refined_query, max_results=max_results), start=1):
            title = result.get("title", "No title")
            href = result.get("href", "")
            body = result.get("body", "")
            snippets.append(f"{idx}. {title}\nURL: {href}\nSnippet: {body}")

    return "\n\n".join(snippets)
