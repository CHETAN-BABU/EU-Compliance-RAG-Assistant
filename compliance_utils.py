"""Compliance RAG utilities for confidence scoring, self-evaluation, and advanced processing."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# Article patterns for GDPR, EU AI Act, DORA
ARTICLE_PATTERNS = {
    "GDPR": r"Article\s+(\d+[a-z]?)",
    "EU AI Act": r"Article\s+(\d+[a-z]?)",
    "DORA": r"Article\s+(\d+[a-z]?)",
}

RECITAL_PATTERN = r"Recital\s+\((\d+)\)"


def extract_article_citations(text: str, regulation: str = "GDPR") -> List[str]:
    """Extract article numbers from legal text."""
    pattern = ARTICLE_PATTERNS.get(regulation, ARTICLE_PATTERNS["GDPR"])
    articles = re.findall(pattern, text, re.IGNORECASE)
    recitals = re.findall(RECITAL_PATTERN, text, re.IGNORECASE)

    citations = [f"{regulation} Article {a}" for a in articles]
    citations.extend([f"{regulation} Recital {r}" for r in recitals])
    return list(dict.fromkeys(citations))  # Remove duplicates, preserve order


def calculate_confidence_score(
    retrieved_docs_count: int,
    avg_similarity_score: float,
    keyword_overlap: float,
    answer_length: int,
) -> Dict[str, float | str]:
    """
    Calculate confidence score based on multiple factors.

    Returns:
        Dict with confidence percentage and breakdown
    """
    # Normalize factors to 0-1
    doc_factor = min(retrieved_docs_count / 5.0, 1.0) * 0.3
    similarity_factor = avg_similarity_score * 0.4
    keyword_factor = keyword_overlap * 0.2
    length_factor = min(answer_length / 500.0, 1.0) * 0.1

    total_confidence = (doc_factor + similarity_factor + keyword_factor + length_factor) * 100
    confidence = min(total_confidence, 95.0)  # Cap at 95%

    return {
        "confidence_score": round(confidence, 1),
        "doc_coverage": f"{min(retrieved_docs_count, 5)}/5",
        "semantic_strength": f"{similarity_factor * 100 / 0.4:.0f}%",
        "keyword_match": f"{keyword_overlap * 100:.0f}%",
        "factors": {
            "retrieval_quality": round(doc_factor * 100 / 0.3, 1),
            "semantic_similarity": round(similarity_factor * 100 / 0.4, 1),
            "keyword_overlap": round(keyword_factor * 100 / 0.2, 1),
            "response_completeness": round(length_factor * 100 / 0.1, 1),
        }
    }


def detect_query_complexity(question: str) -> str:
    """Detect if query is simple, moderate, or complex."""
    # Heuristic: count keywords, length, question marks
    keywords = ["compare", "relationship", "combined", "both", "conflict", "overlap", "integration"]
    regulations = ["gdpr", "ai act", "dora"]

    complexity_score = 0

    # Check for multi-regulation questions
    reg_count = sum(1 for reg in regulations if reg.lower() in question.lower())
    complexity_score += reg_count * 3

    # Check for comparative keywords
    if any(kw in question.lower() for kw in keywords):
        complexity_score += 2

    # Check length and punctuation
    complexity_score += len(question.split()) // 10
    complexity_score += question.count("?")

    if complexity_score >= 5:
        return "complex"
    elif complexity_score >= 2:
        return "moderate"
    return "simple"


def decompose_complex_query(question: str, llm_invoke_func) -> List[Dict[str, str]]:
    """
    Decompose a complex query into sub-queries using LLM.

    Args:
        question: Original question
        llm_invoke_func: Function to call LLM (e.g., llm.invoke)

    Returns:
        List of sub-queries with focus areas
    """
    decomposition_prompt = f"""
You are a legal query decomposition expert. Break this compliance question into focused sub-queries:

Question: {question}

Return exactly 2-3 sub-queries that cover different aspects. Format as JSON array:
[
  {{"sub_query": "...", "focus": "GDPR"}},
  {{"sub_query": "...", "focus": "EU AI Act"}},
]

Return ONLY the JSON array, no other text.
"""

    try:
        result = llm_invoke_func(decomposition_prompt)
        text = result.content if hasattr(result, "content") else str(result)

        # Parse JSON
        import json
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            sub_queries = json.loads(json_match.group())
            return sub_queries if isinstance(sub_queries, list) else []
    except Exception:
        pass

    return []


def generate_self_evaluation(
    question: str,
    answer: str,
    retrieved_docs_count: int,
    llm_invoke_func,
) -> Dict[str, str | bool]:
    """
    Use LLM to self-evaluate answer completeness and accuracy.

    Returns:
        Dict with evaluation results and potential improvements
    """
    evaluation_prompt = f"""
As a compliance expert, evaluate this answer on completeness and accuracy:

Question: {question}

Answer: {answer}

Retrieved sources: {retrieved_docs_count} documents

Provide a JSON evaluation:
{{
  "completeness": 0-100,
  "accuracy": 0-100,
  "issues": ["issue1", "issue2"],
  "improvements": "What should be added",
  "missing_elements": ["element1"]
}}

Return ONLY the JSON, no other text.
"""

    try:
        result = llm_invoke_func(evaluation_prompt)
        text = result.content if hasattr(result, "content") else str(result)

        import json
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            evaluation = json.loads(json_match.group())
            return evaluation
    except Exception:
        pass

    return {
        "completeness": 75,
        "accuracy": 80,
        "issues": [],
        "improvements": "Evaluation unavailable",
        "missing_elements": []
    }


def generate_compliance_checklist(
    topic: str,
    regulations: List[str],
    llm_invoke_func,
) -> Dict[str, List[str]]:
    """
    Generate a compliance checklist for given regulations and topic.

    Args:
        topic: e.g., "AI hiring tool", "Data transfer"
        regulations: List of regulation names
        llm_invoke_func: Function to call LLM

    Returns:
        Dict with checklist items per regulation
    """
    reg_list = ", ".join(regulations)
    checklist_prompt = f"""
Generate a concise compliance checklist for:
Topic: {topic}
Regulations: {reg_list}

Return as JSON:
{{
  "{regulations[0]}": ["item1", "item2"],
  "{regulations[1]}": ["item1", "item2"]
}}

Focus on actionable items. Return ONLY JSON.
"""

    try:
        result = llm_invoke_func(checklist_prompt)
        text = result.content if hasattr(result, "content") else str(result)

        import json
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            checklist = json.loads(json_match.group())
            return checklist
    except Exception:
        pass

    return {reg: ["Item 1", "Item 2", "Item 3"] for reg in regulations}


def format_confidence_display(confidence_data: Dict) -> str:
    """Format confidence data for UI display."""
    score = confidence_data.get("confidence_score", 0)
    doc_coverage = confidence_data.get("doc_coverage", "0/5")
    semantic_str = confidence_data.get("semantic_strength", "0%")
    keyword_match = confidence_data.get("keyword_match", "0%")

    return f"""
**Answer Confidence: {score}%**
- Document Coverage: {doc_coverage} sources
- Semantic Strength: {semantic_str}
- Keyword Match: {keyword_match}
"""


def format_checklist_export(checklist: Dict[str, List[str]], topic: str) -> str:
    """Format checklist for download/export."""
    lines = [f"=== COMPLIANCE CHECKLIST: {topic} ===\n"]

    for regulation, items in checklist.items():
        lines.append(f"\n## {regulation}")
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item}")

    lines.append("\n---\nGenerated by Compliance RAG Assistant\n")
    return "\n".join(lines)
