from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.builders import (
    build_structured_components,
    canonical_workstream,
    uniq,
)

PROVIDER_ORDER = ("pubmed", "europepmc", "openalex", "crossref")

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
    "mediterranean diet": "Diet, Mediterranean",
    "dash diet": "Dietary Approaches To Stop Hypertension",
    "plant-based diet": "Diet, Vegetarian",
    "dietary guidelines": "Guideline",
    "food literacy": "Health Literacy",
    "meal planning": "Food Planning",
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
    mapping = {
        "guideline": "Guideline",
        "guidelines": "Guideline",
        "clinical practice guideline": "Practice Guideline",
        "practice guideline": "Practice Guideline",
        "scientific statement": "Guideline",
        "consensus": "Consensus",
        "position statement": "Guideline",
        "systematic review": "Systematic Review",
        "meta-analysis": "Meta-Analysis",
        "scoping review": "Systematic Review",
        "randomized controlled trial": "Randomized Controlled Trial",
        "controlled trial": "Controlled Clinical Trial",
    }
    for term in uniq(doc_terms):
        pub_type = mapping.get(term.lower())
        if pub_type and pub_type not in publication_types:
            publication_types.append(pub_type)
        else:
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


def _render_pubmed_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
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
    ]
    return uniq([query for query in queries if query])


def _render_europepmc_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
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
    ]
    return uniq([query for query in queries if query])


def _render_openalex_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
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
    ]
    return uniq([query for query in queries if query])


def _render_crossref_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
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
    ]
    return uniq([query for query in queries if query])


def render_queries_for_provider(
    keyword_taxonomy: dict,
    workstream: str,
    provider: str,
) -> list[str]:
    _, components = build_structured_components(keyword_taxonomy, workstream)
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
        provider_querypack[canonical_workstream(workstream)] = workstream_pack
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
        for provider, queries in providers.items():
            for query_order, query_text in enumerate(queries, start=1):
                rows.append(
                    {
                        "workstream": workstream,
                        "provider": provider,
                        "query_order": query_order,
                        "query_text": query_text,
                    }
                )
    csv_lines = ["workstream,provider,query_order,query_text"]
    for row in rows:
        query_text = row["query_text"].replace('"', '""')
        csv_lines.append(
            f'{row["workstream"]},{row["provider"]},{row["query_order"]},"{query_text}"'
        )
    (logs_dir / "provider_querypack_executed.csv").write_text(
        "\n".join(csv_lines) + "\n",
        encoding="utf-8",
    )
