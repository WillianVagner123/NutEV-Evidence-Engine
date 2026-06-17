"""Multilingual and concept-based query expansion for worldwide retrieval.

The keyword taxonomy is written in English, so by default only English-titled
documents are found. This module expands the key concepts of a workstream into
many languages (so documents written in any of them are retrieved) and builds
language-independent MeSH queries for PubMed (MeSH indexes non-English records
under the same controlled descriptor).

The multilingual lexicon lives in ``config/multilingual_lexicon.json`` and is
hashed in the reproducibility report, so a run remains reproducible.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# Maximum rendered terms kept in a single OR-block, to bound query length.
_MAX_BLOCK_TERMS = 60
_MAX_CONDITIONS = 3
_MAX_OTHER = 2


def _uniq(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


@lru_cache(maxsize=8)
def load_lexicon(config_root: str | Path) -> dict:
    """Load the multilingual lexicon JSON; return {} if absent/invalid."""
    path = Path(config_root) / "multilingual_lexicon.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _field_term(term: str, provider: str) -> str:
    clean = str(term).strip()
    if not clean:
        return ""
    if provider == "pubmed":
        return f'"{clean}"[Title/Abstract]'
    if provider in ("europepmc", "preprints"):
        return f'TITLE_ABS:"{clean}"'
    return f'"{clean}"'


def _or_block(terms: list[str], provider: str) -> str:
    rendered = _uniq([_field_term(t, provider) for t in terms if t])[:_MAX_BLOCK_TERMS]
    if not rendered:
        return ""
    if len(rendered) == 1:
        return rendered[0]
    return "(" + " OR ".join(rendered) + ")"


def _join(parts: list[str]) -> str:
    return " AND ".join([part for part in parts if part])


def concept_terms(concept: str, lexicon: dict, languages: list[str] | None = None) -> list[str]:
    """All synonyms of a concept across the requested languages."""
    data = (lexicon.get("concepts") or {}).get(concept) or {}
    langs = languages or lexicon.get("languages") or list(data.keys())
    out: list[str] = []
    for lang in langs:
        out.extend(data.get(lang) or [])
    return _uniq(out)


def active_concepts(component_terms: list[str], lexicon: dict, group: str) -> list[str]:
    """Concept keys in ``group`` whose English synonyms match the given terms."""
    concepts = lexicon.get("concepts") or {}
    group_keys = (lexicon.get("concept_groups") or {}).get(group, [])
    # Ignore very short tokens (<3 chars): substring matching on them produces
    # spurious concept activations (e.g. a stray "a"/"i" matching many concepts).
    terms_lower = [str(t).strip().lower() for t in component_terms if len(str(t).strip()) >= 3]
    matched: list[str] = []
    for concept in group_keys:
        english = [str(t).lower() for t in (concepts.get(concept, {}).get("en") or [])]
        english.append(concept.lower())
        english = [en for en in english if len(en) >= 3]
        for term in terms_lower:
            if any(en in term or term in en for en in english):
                matched.append(concept)
                break
    return _uniq(matched)


def render_multilingual_queries(
    components: dict[str, list[str]],
    lexicon: dict,
    provider: str,
    languages: list[str] | None = None,
) -> list[str]:
    """Bounded set of broad queries that OR each concept across all languages."""
    if not lexicon:
        return []
    languages = languages or lexicon.get("languages")
    conditions = active_concepts(
        list(components.get("condition_terms", [])) + list(components.get("clinical_terms", [])),
        lexicon,
        "conditions",
    )[:_MAX_CONDITIONS]
    diets = active_concepts(
        list(components.get("diet_terms", [])) + list(components.get("nutrition_terms", [])),
        lexicon,
        "diets",
    )[:_MAX_OTHER]
    outcomes = active_concepts(list(components.get("priority_outcomes", [])), lexicon, "outcomes")[:_MAX_OTHER]
    doc_types = active_concepts(list(components.get("doc_type_terms", [])), lexicon, "doc_types")[:_MAX_OTHER]

    def group_block(concepts: list[str]) -> str:
        terms: list[str] = []
        for concept in concepts:
            terms.extend(concept_terms(concept, lexicon, languages))
        return _or_block(terms, provider)

    diet_block = group_block(diets)
    outcome_block = group_block(outcomes)
    doc_block = group_block(doc_types)

    queries: list[str] = []
    for condition in conditions:
        cond_block = _or_block(concept_terms(condition, lexicon, languages), provider)
        if not cond_block:
            continue
        combined = [b for b in (diet_block, outcome_block, doc_block) if b]
        if combined:
            for other in combined:
                queries.append(_join([cond_block, other]))
        else:
            queries.append(cond_block)
    return _uniq([q for q in queries if q])


def render_mesh_queries(components: dict[str, list[str]], lexicon: dict) -> list[str]:
    """Language-independent PubMed MeSH/Publication-Type queries."""
    mesh = lexicon.get("mesh") or {}
    if not mesh:
        return []
    conditions = active_concepts(
        list(components.get("condition_terms", [])) + list(components.get("clinical_terms", [])),
        lexicon,
        "conditions",
    )[:_MAX_CONDITIONS]
    diets = active_concepts(
        list(components.get("diet_terms", [])) + list(components.get("nutrition_terms", [])),
        lexicon,
        "diets",
    )[:_MAX_CONDITIONS]
    doc_types = active_concepts(list(components.get("doc_type_terms", [])), lexicon, "doc_types")[:_MAX_OTHER]

    queries: list[str] = []
    for condition in conditions:
        cm = mesh.get(condition)
        if not cm:
            continue
        cond_clause = f'"{cm}"[MeSH Terms]'
        queries.append(cond_clause)
        for diet in diets:
            dm = mesh.get(diet)
            if dm:
                queries.append(_join([cond_clause, f'"{dm}"[MeSH Terms]']))
        for doc_type in doc_types:
            dm = mesh.get(doc_type)
            if dm:
                queries.append(_join([cond_clause, f'"{dm}"[Publication Type]']))
    return _uniq(queries)
