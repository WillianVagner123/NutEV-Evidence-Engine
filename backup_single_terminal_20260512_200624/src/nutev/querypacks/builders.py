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
    term = str(term).strip()
    if not term:
        return ""
    return f'"{term}"'


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


def chunk_terms(terms: list[str], chunk_size: int = 6) -> list[list[str]]:
    clean = uniq(terms)
    return [clean[i:i + chunk_size] for i in range(0, len(clean), chunk_size)]


def _build_legacy_queries(ws: dict) -> list[str]:
    base = uniq(ws.get("base_terms", []))
    themes = uniq(ws.get("themes", []))
    queries: list[str] = []
    for term in base:
        for theme in themes:
            queries.append(f'"{term}" AND "{theme}"')
    return uniq(queries)


def _join_parts(parts: list[str]) -> str:
    return " AND ".join([p for p in parts if p])


def _specific_queries_busca1(condition_terms, population_terms, doc_type_terms, nutrition_terms, behavior_terms, diet_terms, web_hints):
    out = []
    guideline_terms = [
        "food-based dietary guideline", "dietary guideline", "food guide", "guia alimentar",
        "diretrizes alimentares", "healthy eating recommendation", "nutrition guideline"
    ]
    grey_terms = ["technical report", "policy brief", "white paper", "manual", "framework", "relatório técnico", "nota técnica"]

    out.append(_join_parts([or_block(population_terms, 5), or_block(condition_terms, 6), or_block(guideline_terms, 6)]))
    out.append(_join_parts([or_block(condition_terms, 6), or_block(grey_terms, 6), or_block(nutrition_terms, 6)]))
    out.append(_join_parts([or_block(condition_terms, 6), or_block(diet_terms, 6), or_block(behavior_terms, 6)]))
    out.append(_join_parts([or_block(web_hints, 5), or_block(condition_terms, 6), or_block(doc_type_terms, 6)]))
    return [q for q in out if q]


def _specific_queries_busca2a(condition_terms, clinical_terms, outcome_terms, doc_type_terms, diet_terms):
    out = []
    guideline_terms = ["guideline", "clinical practice guideline", "consensus", "statement", "scientific statement", "position statement", "diretriz", "consenso"]
    clinical_chunks = chunk_terms(condition_terms + clinical_terms, 4)
    outcome_chunks = chunk_terms(outcome_terms, 5)
    for c in clinical_chunks[:8]:
        out.append(_join_parts([or_block(c), or_block(guideline_terms, 6), or_block(outcome_terms, 6)]))
    for o in outcome_chunks[:6]:
        out.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(o), or_block(doc_type_terms, 6)]))
    for d in chunk_terms(diet_terms, 5)[:4]:
        out.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(d), or_block(guideline_terms, 6)]))
    return [q for q in out if q]


def _specific_queries_busca2b(condition_terms, clinical_terms, outcome_terms, behavior_terms, diet_terms):
    out = []
    trial_terms = ["randomized controlled trial", "controlled trial", "pragmatic trial", "pilot study", "feasibility study", "ensaio clínico randomizado", "ensaio controlado"]
    review_terms = ["systematic review", "meta-analysis", "umbrella review", "scoping review", "revisão sistemática", "metanálise"]

    for d in chunk_terms(diet_terms, 4)[:10]:
        out.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(d), or_block(trial_terms, 6), or_block(outcome_terms, 5)]))
        out.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(d), or_block(review_terms, 6), or_block(outcome_terms, 5)]))

    for b in chunk_terms(behavior_terms, 5)[:6]:
        out.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(b), or_block(trial_terms, 6), or_block(outcome_terms, 5)]))

    return [q for q in out if q]


def _specific_queries_a3(condition_terms, clinical_terms, behavior_terms, diet_terms):
    out = []
    instrument_terms = [
        "framework", "questionnaire", "instrument", "index", "food literacy instrument",
        "culinary skills instrument", "commensality", "questionário", "índice"
    ]
    competence_terms = [
        "food literacy", "culinary medicine", "cooking skills", "meal planning",
        "shared meals", "commensality", "behavior change", "self-monitoring"
    ]

    out.append(_join_parts([or_block(instrument_terms, 8), or_block(competence_terms, 8)]))
    out.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(instrument_terms, 8), or_block(behavior_terms, 6)]))
    out.append(_join_parts([or_block(diet_terms, 6), or_block(instrument_terms, 8), or_block(behavior_terms, 6)]))
    return [q for q in out if q]


def build_queries(keyword_taxonomy: dict, workstream: str) -> list[str]:
    ws_key = canonical_workstream(workstream)
    ws = keyword_taxonomy.get("workstreams", {}).get(ws_key, {})
    if not ws:
        return []

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
    behavior_terms = get_global_block(keyword_taxonomy, "implementation_behavior")
    diet_terms = get_global_block(keyword_taxonomy, "diet_patterns")
    nutrition_terms = get_global_block(keyword_taxonomy, "nutrition_domains")

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

    queries.append(_join_parts([or_block(population_terms, 6), or_block(condition_terms + clinical_terms, 8), or_block(doc_type_terms, 6)]))
    queries.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(priority_outcomes, 6), or_block(doc_type_terms, 6)]))
    queries.append(_join_parts([or_block(web_hints, 5), or_block(condition_terms + clinical_terms, 8)]))

    for chunk in chunk_terms(focus_terms, 6)[:12]:
        queries.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(chunk, 6), or_block(doc_type_terms, 6)]))

    for outcome_chunk in chunk_terms(priority_outcomes, 5)[:6]:
        queries.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(outcome_chunk, 5)]))

    for behavior_chunk in chunk_terms(behavior_terms, 5)[:6]:
        queries.append(_join_parts([or_block(condition_terms + clinical_terms, 8), or_block(priority_outcomes, 5), or_block(behavior_chunk, 5)]))

    if ws_key == "busca1":
        queries.extend(_specific_queries_busca1(condition_terms, population_terms, doc_type_terms, nutrition_terms, behavior_terms, diet_terms, web_hints))
    elif ws_key == "busca2a":
        queries.extend(_specific_queries_busca2a(condition_terms, clinical_terms, priority_outcomes, doc_type_terms, diet_terms))
    elif ws_key == "busca2b":
        queries.extend(_specific_queries_busca2b(condition_terms, clinical_terms, priority_outcomes, behavior_terms, diet_terms))
    elif ws_key == "artigo3_framework":
        queries.extend(_specific_queries_a3(condition_terms, clinical_terms, behavior_terms, diet_terms))

    return uniq([q for q in queries if q])


def build_querypack(keyword_taxonomy: dict, workstreams: Iterable[str]) -> dict[str, list[str]]:
    return {ws: build_queries(keyword_taxonomy, ws) for ws in workstreams}