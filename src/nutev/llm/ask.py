"""Retrieval-augmented "ask" layer over the harvested article knowledge base.

The knowledge base is a JSONL corpus (``<kb_dir>/corpus.jsonl``). Retrieval is a
deterministic TF-IDF keyword ranking with no external dependencies, so the layer
works fully offline. When a chat backend is available it answers grounded in the
retrieved sources; otherwise it synthesizes a deterministic structured answer.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from nutev.llm.chat_client import describe_backend, get_chat_client

CORPUS_FILENAME = "corpus.jsonl"
TITLE_WEIGHT = 3
ABSTRACT_TRUNCATE = 600
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

SYSTEM_PROMPT = (
    "You are a careful evidence assistant for a nutrition research knowledge "
    "base. Answer the user's question ONLY using the numbered SOURCES provided. "
    "Cite the sources you use with their bracket indices like [1] or [2]. Do not "
    "invent facts, citations, or numbers that are not present in the sources. If "
    "the supplied evidence is thin or does not cover the question, say so "
    "explicitly rather than guessing."
)


def load_corpus(kb_dir: str | Path) -> list[dict]:
    """Load ``corpus.jsonl`` from ``kb_dir``, skipping blank/bad lines.

    Returns an empty list when the file is missing.
    """

    path = Path(kb_dir) / CORPUS_FILENAME
    if not path.is_file():
        return []
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(obj, dict):
                records.append(obj)
    return records


def _tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in _TOKEN_RE.findall(text or "")]


def _as_text(value: Any) -> str:
    """Flatten a possibly-missing string/list field into searchable text."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return " ".join(_as_text(item) for item in value)
    return str(value)


def _doc_tokens(record: dict) -> list[str]:
    """Build the weighted, tokenized searchable text for one document."""

    title = _as_text(record.get("title"))
    parts = [
        _as_text(record.get("abstract")),
        _as_text(record.get("journal")),
        _as_text(record.get("domains")),
        _as_text(record.get("outcomes")),
        _as_text(record.get("diet_patterns")),
        _as_text(record.get("clinical_conditions")),
        _as_text(record.get("countries")),
        _as_text(record.get("language")),
    ]
    tokens = _tokenize(title) * TITLE_WEIGHT
    for part in parts:
        tokens.extend(_tokenize(part))
    return tokens


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def retrieve(records: list[dict], query: str, k: int = 8) -> list[dict]:
    """Rank ``records`` against ``query`` with deterministic TF-IDF scoring.

    Score = sum over query terms of (term frequency in doc * idf), where
    ``idf = log(N / df)``. Ties break by ``relevance_score`` then
    ``cited_by_count`` (descending), then original order for stability. Each
    returned record is a shallow copy carrying ``_retrieval_score``.
    """

    if not records:
        return []

    query_terms = _tokenize(query)
    doc_tokens = [_doc_tokens(rec) for rec in records]
    doc_counts = [Counter(toks) for toks in doc_tokens]

    total_docs = len(records)
    unique_query_terms = set(query_terms)
    df: dict[str, int] = {}
    for term in unique_query_terms:
        df[term] = sum(1 for counts in doc_counts if counts.get(term))

    idf: dict[str, float] = {}
    for term in unique_query_terms:
        term_df = df[term]
        # log(N/df); guard df==0 so unseen terms contribute nothing.
        idf[term] = math.log(total_docs / term_df) if term_df else 0.0

    scored: list[tuple[float, float, float, int, dict]] = []
    for index, (record, counts) in enumerate(zip(records, doc_counts)):
        score = 0.0
        for term in query_terms:
            tf = counts.get(term, 0)
            if tf:
                score += tf * idf[term]
        scored.append(
            (
                score,
                _to_float(record.get("relevance_score")),
                _to_float(record.get("cited_by_count")),
                index,
                record,
            )
        )

    scored.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))

    results: list[dict] = []
    for score, _rel, _cited, _index, record in scored[: max(0, k)]:
        copy = dict(record)
        copy["_retrieval_score"] = float(score)
        results.append(copy)
    return results


def build_context(records: list[dict]) -> str:
    """Render retrieved records as compact numbered context blocks."""

    blocks: list[str] = []
    for i, record in enumerate(records, start=1):
        title = _as_text(record.get("title")).strip() or "Untitled"
        year = record.get("year")
        year_str = str(year) if year not in (None, "") else "n.d."
        countries = _as_text(record.get("countries")).strip() or "n/a"
        journal = _as_text(record.get("journal")).strip() or "n/a"
        ref = _as_text(record.get("doi")).strip() or _as_text(record.get("url")).strip()
        ref = ref or "no doi/url"
        abstract = _as_text(record.get("abstract")).strip()
        if len(abstract) > ABSTRACT_TRUNCATE:
            abstract = abstract[:ABSTRACT_TRUNCATE].rstrip() + "..."
        if not abstract:
            abstract = "(no abstract available)"
        header = f"[{i}] {title} ({year_str}; {countries}; {journal}) {ref}"
        blocks.append(f"{header}\n    {abstract}")
    return "\n\n".join(blocks)


def _citation(index: int, record: dict) -> dict:
    return {
        "index": index,
        "document_id": record.get("document_id"),
        "title": record.get("title"),
        "year": record.get("year"),
        "countries": record.get("countries"),
        "journal": record.get("journal"),
        "doi": record.get("doi"),
        "url": record.get("url"),
    }


def _offline_answer(question: str, context: str, n_hits: int) -> str:
    if n_hits == 0:
        return (
            "No matching sources were found in the knowledge base for this "
            "question, so no grounded answer can be given.\n\n"
            f"Question: {question}"
        )
    return (
        f"Offline retrieval-only mode (no chat backend configured).\n"
        f"Showing the {n_hits} most relevant source(s) for: {question}\n\n"
        f"SOURCES:\n{context}"
    )


def answer(
    question: str,
    kb_dir: str | Path,
    k: int = 8,
    client: object | str = "auto",
) -> dict:
    """Answer ``question`` from the knowledge base in ``kb_dir``.

    With a chat backend available the answer is grounded in retrieved sources;
    any client error falls back to deterministic offline mode. The returned
    dict keys are a stable contract.
    """

    records = load_corpus(kb_dir)
    top = retrieve(records, question, k=k)
    context = build_context(top)
    citations = [_citation(i, rec) for i, rec in enumerate(top, start=1)]

    chat = get_chat_client() if client == "auto" else client

    mode = "offline"
    backend = "offline"
    answer_text = _offline_answer(question, context, len(top))

    if chat is not None and top:
        user = f"{question}\n\nSOURCES:\n{context}"
        try:
            llm_text = chat.chat(SYSTEM_PROMPT, user)
            if llm_text and llm_text.strip():
                answer_text = llm_text
                mode = "llm"
                backend = describe_backend() or "offline"
        except Exception:  # noqa: BLE001 - any backend failure -> offline
            mode = "offline"
            backend = "offline"
            answer_text = _offline_answer(question, context, len(top))

    return {
        "question": question,
        "mode": mode,
        "backend": backend,
        "answer": answer_text,
        "citations": citations,
        "n_corpus": len(records),
    }
