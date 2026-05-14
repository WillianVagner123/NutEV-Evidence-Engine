from __future__ import annotations

from collections.abc import Iterable


WORKSTREAM_ALIASES = {
    "a3": "artigo3_framework",
    "article3": "artigo3_framework",
}


def canonical_workstream(workstream: str) -> str:
    return WORKSTREAM_ALIASES.get(workstream, workstream)


def uniq(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if not item:
            continue
        value = str(item).strip()
        if not value:
            continue
        low = value.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(value)
    return out


def quote_term(term: str) -> str:
    term = term.strip()
    if not term:
        return ""
    if " " in term or "-" in term or "/" in term:
        return f'"{term}"'
    return term


def or_block(terms: list[str], limit: int | None = None) -> str:
    chunk = uniq(terms)
    if limit is not None:
        chunk = chunk[:limit]
    chunk = [quote_term(t) for t in chunk if t]
    if not chunk:
        return ""
    if len(chunk) == 1:
        return chunk[0]
    return "(" + " OR ".join(chunk) + ")"


def flatten_dict_lists(d: dict) -> list[str]:
    out: list[str] = []
    for value in d.values():
        if isinstance(value, list):
            out.extend(value)
        elif isinstance(value, dict):
            out.extend(flatten_dict_lists(value))
    return out


def get_global_block(keyword_taxonomy: dict, block_name: str) -> list[str]:
    global_cfg = keyword_taxonomy.get("global", {})
    block = global_cfg.get(block_name, {})

    if isinstance(block, list):
        return uniq(block)
    if isinstance(block, dict):
        return uniq(flatten_dict_lists(block))
    return []


def get_named_terms(section: dict, keys: list[str]) -> list[str]:
    out: list[str] = []
    for key in keys:
        value = section.get(key, [])
        if isinstance(value, list):
            out.extend(value)
    return uniq(out)


def chunk_terms(terms: list[str], chunk_size: int = 8) -> list[list[str]]:
    clean = uniq(terms)
    return [clean[i:i + chunk_size] for i in range(0, len(clean), chunk_size)]


def _build_legacy_queries(ws: dict) -> list[str]:
    # compatibilidade com teste antigo
    base = uniq(ws.get("base_terms", []))
    themes = uniq(ws.get("themes", []))
    queries: list[str] = []

    for term in base:
        for theme in themes:
            queries.append(f'"{term}" AND "{theme}"')

    return uniq(queries)


def build_queries(keyword_taxonomy: dict, workstream: str) -> list[str]:
    ws_key = canonical_workstream(workstream)
    ws = keyword_taxonomy.get("workstreams", {}).get(ws_key, {})
    if not ws:
        return []

    # compatibilidade com formato antigo
    if ws.get("base_terms") and ws.get("themes"):
        return _build_legacy_queries(ws)

    global_cfg = keyword_taxonomy.get("global", {})
    clinical_cfg = keyword_taxonomy.get("clinical", {})
    outcomes_cfg = keyword_taxonomy.get("outcomes", {})

    population_terms = uniq(ws.get("population_terms", []))
    condition_terms = uniq(ws.get("condition_terms", []))
    clinical_terms = get_named_terms(clinical_cfg, ws.get("clinical_keys", []))
    priority_outcomes = get_named_terms(outcomes_cfg, ws.get("priority_outcomes", []))
    doc_type_terms = get_named_terms(global_cfg.get("document_types", {}), ws.get("document_type_keys", []))
    web_hints = uniq(ws.get("web_query_hints", []))

    focus_terms: list[str] = []
    for block_name in ws.get("focus_blocks", []):
        focus_terms.extend(get_global_block(keyword_taxonomy, block_name))
    focus_terms = uniq(focus_terms)

    title = ws.get("title", "")
    research_question = ws.get("research_question", "")

    queries: list[str] = []

    if title:
        queries.append(title)
    if research_question:
        queries.append(research_question)

    q = " AND ".join(
        part for part in [
            or_block(population_terms, 6),
            or_block(condition_terms, 8),
            or_block(doc_type_terms, 8),
        ] if part
    )
    if q:
        queries.append(q)

    q = " AND ".join(
        part for part in [
            or_block(condition_terms + clinical_terms, 10),
            or_block(priority_outcomes, 8),
        ] if part
    )
    if q:
        queries.append(q)

    q = " AND ".join(
        part for part in [
            or_block(web_hints, 6),
            or_block(condition_terms + clinical_terms, 8),
        ] if part
    )
    if q:
        queries.append(q)

    focus_chunks = chunk_terms(focus_terms, 8)
    for chunk in focus_chunks[:6]:
        q = " AND ".join(
            part for part in [
                or_block(condition_terms + clinical_terms, 8),
                or_block(chunk),
                or_block(doc_type_terms, 6),
            ] if part
        )
        if q:
            queries.append(q)

    behavior_terms = get_global_block(keyword_taxonomy, "implementation_behavior")
    behavior_chunks = chunk_terms(behavior_terms, 8)
    for chunk in behavior_chunks[:3]:
        q = " AND ".join(
            part for part in [
                or_block(condition_terms + clinical_terms, 8),
                or_block(priority_outcomes, 6),
                or_block(chunk),
            ] if part
        )
        if q:
            queries.append(q)

    return uniq(queries)


def build_querypack(keyword_taxonomy: dict, workstreams: Iterable[str]) -> dict[str, list[str]]:
    return {ws: build_queries(keyword_taxonomy, ws) for ws in workstreams}