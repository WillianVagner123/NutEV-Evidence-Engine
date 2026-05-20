from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.builders import (
    build_structured_components,
    canonical_workstream,
    chunk_terms,
    uniq,
)
from nutev.querypacks.semantic_blocks import prioritized_semantic_blocks, semantic_terms

PROVIDER_ORDER = ("pubmed", "europepmc", "openalex", "crossref")
LIVER_FOCUSED_WORKSTREAMS = {"busca2a", "busca2b"}

PUBMED_MESH_MAP = {
    "obesity": "Obesity",
    "overweight": "Overweight",
    "diabetes": "Diabetes Mellitus, Type 2",
    "type 2 diabetes": "Diabetes Mellitus, Type 2",
    "hypertension": "Hypertension",
    "dyslipidemia": "Dyslipidemias",
    "cardiovascular disease": "Cardiovascular Diseases",
    "cardiometabolic risk": "Cardiovascular Diseases",
    "metabolic syndrome": "Metabolic Syndrome",
    "nafld": "Non-alcoholic Fatty Liver Disease",
    "masld": "Non-alcoholic Fatty Liver Disease",
    "mafld": "Non-alcoholic Fatty Liver Disease",
    "mediterranean diet": "Diet, Mediterranean",
    "dash diet": "Dietary Approaches To Stop Hypertension",
    "plant-based diet": "Diet, Vegetarian",
    "dietary guidelines": "Guideline",
    "food literacy": "Health Literacy",
    "nutrition literacy": "Health Literacy",
    "meal planning": "Food Planning",
    "implementation science": "Implementation Science",
}

CARDIOMETABOLIC_LIVER_TERMS = [
    "masld",
    "nafld",
    "mafld",
    "mash",
    "nash",
    "fatty liver",
    "steatotic liver disease",
    "steatohepatitis",
    "metabolic dysfunction-associated steatotic liver disease",
    "metabolic dysfunction-associated fatty liver disease",
    "metabolic dysfunction associated fatty liver disease",
    "nonalcoholic fatty liver disease",
    "non-alcoholic fatty liver disease",
    "nonalcoholic steatohepatitis",
    "non-alcoholic steatohepatitis",
]

CARDIOMETABOLIC_LIVER_HINTS = [
    "masld",
    "nafld",
    "mafld",
    "mash",
    "nash",
    "steatohepatitis",
    "steatotic liver disease",
    "fatty liver",
]

PUBMED_DOCUMENT_TYPE_MAP = {
    "guideline": "Guideline",
    "guidelines": "Guideline",
    "clinical practice guideline": "Practice Guideline",
    "practice guideline": "Practice Guideline",
    "practice advisory": "Practice Guideline",
    "practice guidance": "Practice Guideline",
    "living guideline": "Guideline",
    "guideline update": "Guideline",
    "scientific statement": "Guideline",
    "guidance statement": "Guideline",
    "joint statement": "Guideline",
    "consensus": "Consensus",
    "consensus statement": "Consensus",
    "consensus report": "Consensus",
    "expert consensus": "Consensus",
    "clinical consensus": "Consensus",
    "position statement": "Guideline",
    "position paper": "Guideline",
    "practice recommendation": "Guideline",
    "standards of care": "Guideline",
    "systematic review": "Systematic Review",
    "umbrella review": "Systematic Review",
    "overview of reviews": "Systematic Review",
    "review of reviews": "Systematic Review",
    "meta-analysis": "Meta-Analysis",
    "scoping review": "Systematic Review",
    "randomized controlled trial": "Randomized Controlled Trial",
    "controlled trial": "Controlled Clinical Trial",
}


def _provider_field_term(term: str, provider: str) -> str:
    clean = str(term).strip()
    if not clean:
        return ""
    if provider == "pubmed":
        return f'"{clean}"[Title/Abstract]'
    if provider == "europepmc":
        return f'TITLE_ABS:"{clean}"'
    return f'"{clean}"'


def _provider_or_block(
    terms: list[str],
    provider: str,
    limit: int | None = None,
) -> str:
    chunk = uniq(terms)
    if limit is not None:
        chunk = chunk[:limit]
    rendered = [_provider_field_term(term, provider) for term in chunk if term]
    if not rendered:
        return ""
    if len(rendered) == 1:
        return rendered[0]
    return "(" + " OR ".join(rendered) + ")"


def _pubmed_mesh_block(terms: list[str], limit: int = 6) -> str:
    mesh_terms: list[str] = []
    for term in uniq(terms):
        mesh = PUBMED_MESH_MAP.get(term.lower())
        if mesh and mesh not in mesh_terms:
            mesh_terms.append(mesh)
    if limit is not None:
        mesh_terms = mesh_terms[:limit]
    if not mesh_terms:
        return ""
    rendered = [f'"{term}"[MeSH Terms]' for term in mesh_terms]
    if len(rendered) == 1:
        return rendered[0]
    return "(" + " OR ".join(rendered) + ")"


def _join_parts(parts: list[str]) -> str:
    return " AND ".join([part for part in parts if part])


def _pubmed_document_clause(doc_terms: list[str]) -> str:
    publication_types = []
    title_abs_terms = []
    for term in uniq(doc_terms):
        pub_type = PUBMED_DOCUMENT_TYPE_MAP.get(term.lower())
        if pub_type:
            if pub_type not in publication_types:
                publication_types.append(pub_type)
            continue
        title_abs_terms.append(term)
    publication_block = ""
    if publication_types:
        publication_block = "(" + " OR ".join(
            [f'"{value}"[Publication Type]' for value in publication_types]
        ) + ")"
    return _join_parts(
        [
            publication_block,
            _provider_or_block(title_abs_terms, "pubmed", 6),
        ]
    )


def _augment_with_semantic_blocks(
    workstream: str,
    components: dict[str, list[str]],
) -> dict[str, list[str]]:
    enriched = {key: list(value) for key, value in components.items()}
    high_priority_terms = semantic_terms(workstream, min_priority=4)
    broad_terms = semantic_terms(workstream, min_priority=3)
    semantic_doc_terms = semantic_terms(
        workstream,
        field="document_terms",
        min_priority=3,
    )
    block_priorities = [
        f"{item['name']}:{item['priority']}"
        for item in prioritized_semantic_blocks(workstream)
    ]
    focus_terms = enriched.get("focus_terms", [])

    enriched["web_hints"] = uniq(enriched.get("web_hints", []) + high_priority_terms)
    enriched["behavior_terms"] = uniq(enriched.get("behavior_terms", []) + broad_terms)
    enriched["focus_terms"] = uniq(focus_terms + broad_terms)
    enriched["doc_type_terms"] = uniq(
        enriched.get("doc_type_terms", []) + semantic_doc_terms
    )
    if canonical_workstream(workstream) in LIVER_FOCUSED_WORKSTREAMS:
        # Keep MASLD/NAFLD guideline and intervention evidence visible even
        # when broader cardiometabolic condition lists are capped for query size.
        enriched["condition_terms"] = uniq(
            enriched.get("condition_terms", []) + CARDIOMETABOLIC_LIVER_TERMS
        )
        enriched["clinical_terms"] = uniq(
            enriched.get("clinical_terms", []) + CARDIOMETABOLIC_LIVER_TERMS
        )
        enriched["web_hints"] = uniq(
            enriched.get("web_hints", []) + CARDIOMETABOLIC_LIVER_HINTS
        )
    # Put workstream focus terms first so provider query caps do not crowd out
    # clinically important, NutMEV-specific expansions.
    enriched["semantic_terms"] = uniq(focus_terms + broad_terms)
    enriched["semantic_block_priorities"] = block_priorities
    return enriched


def _secondary_condition_chunks(
    components: dict[str, list[str]],
    *,
    primary_limit: int = 8,
) -> list[list[str]]:
    combined_conditions = uniq(
        components.get("condition_terms", []) + components.get("clinical_terms", [])
    )
    if len(combined_conditions) <= primary_limit:
        return []
    return chunk_terms(combined_conditions[primary_limit:], 4)[:3]


def _render_overflow_condition_queries(
    components: dict[str, list[str]],
    provider: str,
) -> list[str]:
    queries: list[str] = []
    for extra_conditions in _secondary_condition_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_conditions, provider, 4),
                    _provider_or_block(components["diet_terms"], provider, 4),
                    _provider_or_block(components["priority_outcomes"], provider, 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_conditions, provider, 4),
                    _provider_or_block(components["behavior_terms"], provider, 4),
                    _provider_or_block(components["doc_type_terms"], provider, 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_pubmed_overflow_condition_queries(
    components: dict[str, list[str]],
) -> list[str]:
    queries: list[str] = []
    for extra_conditions in _secondary_condition_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_conditions, "pubmed", 4),
                    _provider_or_block(components["diet_terms"], "pubmed", 4),
                    _provider_or_block(components["priority_outcomes"], "pubmed", 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_conditions, "pubmed", 4),
                    _provider_or_block(components["behavior_terms"], "pubmed", 4),
                    _pubmed_document_clause(components["doc_type_terms"]),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_pubmed_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    semantic_terms_ = components.get("semantic_terms", [])
    queries = [
        _join_parts(
            [
                _provider_or_block(components["population_terms"], "pubmed", 6),
                _join_parts(
                    [
                        _provider_or_block(condition_terms, "pubmed", 8),
                        _pubmed_mesh_block(condition_terms, 4),
                    ]
                ),
                _pubmed_document_clause(components["doc_type_terms"]),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(condition_terms, "pubmed", 8),
                _provider_or_block(components["priority_outcomes"], "pubmed", 6),
                _pubmed_document_clause(components["doc_type_terms"]),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["diet_terms"], "pubmed", 5),
                _provider_or_block(condition_terms, "pubmed", 8),
                _provider_or_block(components["priority_outcomes"], "pubmed", 5),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["behavior_terms"], "pubmed", 5),
                _provider_or_block(condition_terms, "pubmed", 8),
                _provider_or_block(components["priority_outcomes"], "pubmed", 5),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["web_hints"], "pubmed", 4),
                _provider_or_block(components["nutrition_terms"], "pubmed", 5),
                _provider_or_block(condition_terms, "pubmed", 6),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(semantic_terms_, "pubmed", 5),
                _provider_or_block(condition_terms, "pubmed", 6),
                _pubmed_document_clause(components["doc_type_terms"]),
            ]
        ),
    ]
    return uniq(
        [query for query in queries if query]
        + _render_pubmed_overflow_condition_queries(components)
    )


def _render_europepmc_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    semantic_terms_ = components.get("semantic_terms", [])
    queries = [
        _join_parts(
            [
                _provider_or_block(components["population_terms"], "europepmc", 6),
                _provider_or_block(condition_terms, "europepmc", 8),
                _provider_or_block(components["doc_type_terms"], "europepmc", 6),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(condition_terms, "europepmc", 8),
                _provider_or_block(components["priority_outcomes"], "europepmc", 6),
                _provider_or_block(components["doc_type_terms"], "europepmc", 6),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["diet_terms"], "europepmc", 5),
                _provider_or_block(condition_terms, "europepmc", 8),
                _provider_or_block(components["priority_outcomes"], "europepmc", 5),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["behavior_terms"], "europepmc", 5),
                _provider_or_block(condition_terms, "europepmc", 8),
                _provider_or_block(components["priority_outcomes"], "europepmc", 5),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(semantic_terms_, "europepmc", 5),
                _provider_or_block(condition_terms, "europepmc", 8),
                _provider_or_block(components["doc_type_terms"], "europepmc", 5),
            ]
        ),
    ]
    return uniq(
        [query for query in queries if query]
        + _render_overflow_condition_queries(components, "europepmc")
    )


def _render_openalex_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    semantic_terms_ = components.get("semantic_terms", [])
    queries = [
        _join_parts(
            [
                _provider_or_block(condition_terms, "openalex", 6),
                _provider_or_block(components["doc_type_terms"], "openalex", 4),
                _provider_or_block(components["priority_outcomes"], "openalex", 4),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["diet_terms"], "openalex", 4),
                _provider_or_block(condition_terms, "openalex", 6),
                _provider_or_block(components["priority_outcomes"], "openalex", 4),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["behavior_terms"], "openalex", 4),
                _provider_or_block(condition_terms, "openalex", 6),
                _provider_or_block(components["doc_type_terms"], "openalex", 4),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(semantic_terms_, "openalex", 4),
                _provider_or_block(condition_terms, "openalex", 6),
                _provider_or_block(components["priority_outcomes"], "openalex", 4),
            ]
        ),
    ]
    return uniq(
        [query for query in queries if query]
        + _render_overflow_condition_queries(components, "openalex")
    )


def _render_crossref_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    semantic_terms_ = components.get("semantic_terms", [])
    queries = [
        _join_parts(
            [
                _provider_or_block(condition_terms, "crossref", 6),
                _provider_or_block(components["doc_type_terms"], "crossref", 4),
                _provider_or_block(components["priority_outcomes"], "crossref", 4),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["diet_terms"], "crossref", 4),
                _provider_or_block(condition_terms, "crossref", 6),
                _provider_or_block(components["behavior_terms"], "crossref", 4),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(components["web_hints"], "crossref", 4),
                _provider_or_block(condition_terms, "crossref", 6),
                _provider_or_block(components["doc_type_terms"], "crossref", 4),
            ]
        ),
        _join_parts(
            [
                _provider_or_block(semantic_terms_, "crossref", 4),
                _provider_or_block(condition_terms, "crossref", 6),
                _provider_or_block(components["doc_type_terms"], "crossref", 4),
            ]
        ),
    ]
    return uniq(
        [query for query in queries if query]
        + _render_overflow_condition_queries(components, "crossref")
    )


def render_queries_for_provider(
    keyword_taxonomy: dict,
    workstream: str,
    provider: str,
) -> list[str]:
    _, components = build_structured_components(keyword_taxonomy, workstream)
    components = _augment_with_semantic_blocks(workstream, components)
    if provider == "pubmed":
        return _render_pubmed_queries(components)
    if provider == "europepmc":
        return _render_europepmc_queries(components)
    if provider == "openalex":
        return _render_openalex_queries(components)
    if provider == "crossref":
        return _render_crossref_queries(components)
    return []


def build_provider_querypack(
    keyword_taxonomy: dict,
    workstreams: list[str],
    providers_by_workstream: dict[str, list[str]],
) -> dict[str, dict[str, list[str]]]:
    provider_querypack: dict[str, dict[str, list[str]]] = {}
    for workstream in workstreams:
        workstream_pack: dict[str, list[str]] = {}
        for provider in providers_by_workstream.get(workstream, []):
            if provider == "official_web":
                continue
            if provider not in PROVIDER_ORDER:
                continue
            workstream_pack[provider] = render_queries_for_provider(
                keyword_taxonomy,
                workstream,
                provider,
            )
        # Keep the requested workstream key in the querypack. Query rendering
        # already resolves aliases internally, and preserving the input name
        # avoids duplicate audit rows for alias/canonical pairs.
        provider_querypack[workstream] = workstream_pack
    return provider_querypack


def write_provider_querypack_audit(
    provider_querypack: dict[str, dict[str, list[str]]],
    logs_dir: Path,
) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "provider_querypack_executed.json").write_text(
        json.dumps(provider_querypack, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rows = []
    for workstream, providers in provider_querypack.items():
        block_priorities = ";".join(
            [
                f"{item['name']}:{item['priority']}"
                for item in prioritized_semantic_blocks(workstream)
            ]
        )
        for provider, queries in providers.items():
            for query_order, query_text in enumerate(queries, start=1):
                rows.append(
                    {
                        "workstream": workstream,
                        "provider": provider,
                        "query_order": query_order,
                        "semantic_blocks": block_priorities,
                        "query_text": query_text,
                    }
                )
    csv_lines = ["workstream,provider,query_order,semantic_blocks,query_text"]
    for row in rows:
        query_text = row["query_text"].replace('"', '""')
        semantic_blocks = row["semantic_blocks"].replace('"', '""')
        csv_lines.append(
            f'{row["workstream"]},{row["provider"]},{row["query_order"]},'
            f'"{semantic_blocks}","{query_text}"'
        )
    (logs_dir / "provider_querypack_executed.csv").write_text(
        "\n".join(csv_lines) + "\n",
        encoding="utf-8",
    )