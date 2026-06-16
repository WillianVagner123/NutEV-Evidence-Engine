from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.builders import (
    build_structured_components,
    canonical_workstream,
    chunk_terms,
    uniq,
)
from nutev.querypacks.multilingual import (
    render_mesh_queries,
    render_multilingual_queries,
)
from nutev.querypacks.semantic_blocks import prioritized_semantic_blocks, semantic_terms

PROVIDER_ORDER = ("pubmed", "europepmc", "openalex", "crossref", "semantic_scholar", "doaj", "scielo", "preprints", "clinicaltrials", "core")
LIVER_FOCUSED_WORKSTREAMS = {"busca2a", "busca2b"}
BUSCA2A_GUIDANCE_TERMS = [
    "practice guideline",
    "clinical practice guideline",
    "practice guidance",
    "guidance statement",
    "consensus statement",
    "consensus guidance",
    "scientific statement",
    "guideline update",
    "clinical practice update",
    "best practice advice",
    "standards of care",
    "clinical decision pathway",
    "position statement",
    "position paper",
    "consensus report",
    "joint statement",
    "joint guideline",
    "clinical practice recommendation",
    "clinical practice recommendations",
    "scientific advisory",
    "decision pathway",
    "clinical guidance",
    "living guideline",
]
BEHAVIOR_PRIORITY_TERMS = [
    "implementation science",
    "implementation research",
    "implementation fidelity",
    "implementation determinant",
    "implementation determinants",
    "implementation evaluation",
    "shared decision making",
    "motivational interviewing",
    "behavior change technique",
    "self-management support",
    "dietary adherence",
    "treatment adherence",
    "registered dietitian",
    "registered dietitian nutritionist",
    "dietitian-led intervention",
    "dietitian led intervention",
    "food is medicine",
    "food as medicine",
    "food is medicine intervention",
    "produce prescription",
    "produce prescriptions",
    "produce prescription program",
    "medically tailored meals",
    "medically tailored groceries",
]

PUBMED_MESH_MAP = {
    "obesity": "Obesity",
    "overweight": "Overweight",
    "diabetes": "Diabetes Mellitus, Type 2",
    "type 2 diabetes": "Diabetes Mellitus, Type 2",
    "prediabetes": "Prediabetic State",
    "insulin resistance": "Insulin Resistance",
    "hypertension": "Hypertension",
    "dyslipidemia": "Dyslipidemias",
    "dyslipidaemia": "Dyslipidemias",
    "hyperlipidemia": "Hyperlipidemias",
    "hyperlipidaemia": "Hyperlipidemias",
    "hypercholesterolemia": "Hypercholesterolemia",
    "hypercholesterolaemia": "Hypercholesterolemia",
    "hypertriglyceridemia": "Hypertriglyceridemia",
    "hypertriglyceridaemia": "Hypertriglyceridemia",
    "atherogenic dyslipidemia": "Dyslipidemias",
    "atherogenic dyslipidaemia": "Dyslipidemias",
    "apolipoprotein b": "Apolipoproteins B",
    "apo b": "Apolipoproteins B",
    "cardiovascular disease": "Cardiovascular Diseases",
    "cardiometabolic risk": "Cardiovascular Diseases",
    "metabolic syndrome": "Metabolic Syndrome",
    "nafld": "Non-alcoholic Fatty Liver Disease",
    "masld": "Non-alcoholic Fatty Liver Disease",
    "mafld": "Non-alcoholic Fatty Liver Disease",
    "mash": "Steatohepatitis",
    "nash": "Steatohepatitis",
    "fatty liver": "Fatty Liver",
    "steatotic liver disease": "Fatty Liver",
    "nonalcoholic fatty liver disease": "Non-alcoholic Fatty Liver Disease",
    "non-alcoholic fatty liver disease": "Non-alcoholic Fatty Liver Disease",
    "nonalcoholic steatohepatitis": "Steatohepatitis",
    "non-alcoholic steatohepatitis": "Steatohepatitis",
    "metabolic dysfunction-associated fatty liver disease": "Non-alcoholic Fatty Liver Disease",
    "metabolic dysfunction associated fatty liver disease": "Non-alcoholic Fatty Liver Disease",
    "metabolic dysfunction-associated steatotic liver disease": "Non-alcoholic Fatty Liver Disease",
    "metabolic dysfunction associated steatotic liver disease": "Non-alcoholic Fatty Liver Disease",
    "metabolic dysfunction-associated steatohepatitis": "Steatohepatitis",
    "metabolic dysfunction associated steatohepatitis": "Steatohepatitis",
    "mediterranean diet": "Diet, Mediterranean",
    "dash diet": "Dietary Approaches To Stop Hypertension",
    "plant-based diet": "Diet, Vegetarian",
    "dietary guidelines": "Guideline",
    "food literacy": "Health Literacy",
    "nutrition literacy": "Health Literacy",
    "meal planning": "Food Planning",
    "implementation science": "Implementation Science",
    "lifestyle medicine": "Life Style",
    "lifestyle intervention": "Life Style",
    "lifestyle modification": "Life Style",
    "therapeutic lifestyle changes": "Life Style",
    "therapeutic lifestyle change": "Life Style",
    "medical nutrition therapy": "Diet Therapy",
    "nutrition counseling": "Counseling",
    "nutrition counselling": "Counseling",
    "dietary counseling": "Counseling",
    "dietary counselling": "Counseling",
    "registered dietitian": "Dietitians",
    "registered dietitian nutritionist": "Dietitians",
    "shared decision making": "Decision Making, Shared",
    "self-efficacy": "Self Efficacy",
    "self efficacy": "Self Efficacy",
    "cooking skills": "Cooking",
    "cooking confidence": "Cooking",
    "home cooking": "Cooking",
    "teaching kitchen": "Cooking",
    "teaching kitchens": "Cooking",
    "food environment": "Food Supply",
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
    "metabolic dysfunction-associated steatohepatitis",
    "metabolic dysfunction associated steatohepatitis",
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
    "metabolic dysfunction-associated steatohepatitis",
    "metabolic dysfunction associated steatohepatitis",
]

PUBMED_DOCUMENT_TYPE_MAP = {
    "guideline": "Guideline",
    "guidelines": "Guideline",
    "guideline update": "Guideline",
    "standards of care": "Guideline",
    "standards of medical care": "Guideline",
    "standards of medical care in diabetes": "Guideline",
    "guidance statement": "Guideline",
    "joint statement": "Guideline",
    "joint guideline": "Guideline",
    "living guideline": "Guideline",
    "scientific statement": "Guideline",
    "position statement": "Guideline",
    "position paper": "Guideline",
    "clinical guidance": "Guideline",
    "clinical practice guideline": "Practice Guideline",
    "practice guideline": "Practice Guideline",
    "practice advisory": "Practice Guideline",
    "practice guidance": "Practice Guideline",
    "clinical decision pathway": "Practice Guideline",
    "decision pathway": "Practice Guideline",
    "clinical practice update": "Practice Guideline",
    "clinical practice recommendation": "Practice Guideline",
    "clinical practice recommendations": "Practice Guideline",
    "consensus": "Consensus",
    "consensus statement": "Consensus",
    "expert consensus": "Consensus",
    "clinical consensus": "Consensus",
    "consensus guidance": "Consensus",
    "consensus report": "Consensus",
    "systematic review": "Systematic Review",
    "umbrella review": "Systematic Review",
    "overview of reviews": "Systematic Review",
    "review of reviews": "Systematic Review",
    "meta-analysis": "Meta-Analysis",
    "meta analysis": "Meta-Analysis",
    "network meta-analysis": "Meta-Analysis",
    "network meta analysis": "Meta-Analysis",
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


def _pubmed_mesh_expansion_queries(components: dict[str, list[str]]) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    focus_mesh_block = _pubmed_mesh_block(
        uniq(
            components.get("focus_terms", [])
            + components.get("behavior_terms", [])
            + components.get("nutrition_terms", [])
            + components.get("web_hints", [])
        ),
        4,
    )
    diet_mesh_block = _pubmed_mesh_block(
        uniq(components.get("diet_terms", []) + components.get("focus_terms", [])),
        4,
    )
    queries: list[str] = []
    if focus_mesh_block:
        queries.append(
            _join_parts(
                [
                    _provider_or_block(condition_terms, "pubmed", 6),
                    focus_mesh_block,
                    _pubmed_document_clause(components["doc_type_terms"]),
                ]
            )
        )
    if diet_mesh_block:
        queries.append(
            _join_parts(
                [
                    _provider_or_block(condition_terms, "pubmed", 6),
                    diet_mesh_block,
                    _provider_or_block(components["priority_outcomes"], "pubmed", 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


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
    behavior_seed_terms = enriched.get("behavior_terms", [])
    behavior_priority_terms = [
        term
        for term in BEHAVIOR_PRIORITY_TERMS
        if term in broad_terms or term in behavior_seed_terms or canonical_workstream(workstream) == "busca2b"
    ]

    if canonical_workstream(workstream) == "busca2a":
        enriched["doc_type_terms"] = uniq(
            BUSCA2A_GUIDANCE_TERMS + enriched.get("doc_type_terms", [])
        )
        enriched["web_hints"] = uniq(
            BUSCA2A_GUIDANCE_TERMS + enriched.get("web_hints", [])
        )

    enriched["web_hints"] = uniq(enriched.get("web_hints", []) + high_priority_terms)
    enriched["behavior_terms"] = uniq(
        behavior_priority_terms + behavior_seed_terms + broad_terms
    )
    enriched["focus_terms"] = uniq(focus_terms + broad_terms)
    enriched["doc_type_terms"] = uniq(
        enriched.get("doc_type_terms", []) + semantic_doc_terms
    )
    if canonical_workstream(workstream) in LIVER_FOCUSED_WORKSTREAMS:
        enriched["condition_terms"] = uniq(
            enriched.get("condition_terms", []) + CARDIOMETABOLIC_LIVER_TERMS
        )
        enriched["clinical_terms"] = uniq(
            enriched.get("clinical_terms", []) + CARDIOMETABOLIC_LIVER_TERMS
        )
        enriched["web_hints"] = uniq(
            enriched.get("web_hints", []) + CARDIOMETABOLIC_LIVER_HINTS
        )
    enriched["semantic_terms"] = uniq(
        high_priority_terms + enriched.get("focus_terms", []) + broad_terms
    )
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


def _secondary_behavior_chunks(
    components: dict[str, list[str]],
    *,
    primary_limit: int = 5,
) -> list[list[str]]:
    behavior_terms = uniq(components.get("behavior_terms", []))
    if len(behavior_terms) <= primary_limit:
        return []
    return chunk_terms(behavior_terms[primary_limit:], 4)[:4]


def _secondary_doc_type_chunks(
    components: dict[str, list[str]],
    *,
    primary_limit: int = 6,
) -> list[list[str]]:
    doc_type_terms = uniq(components.get("doc_type_terms", []))
    if len(doc_type_terms) <= primary_limit:
        return []
    return chunk_terms(doc_type_terms[primary_limit:], 4)[:4]


def _secondary_outcome_chunks(
    components: dict[str, list[str]],
    *,
    primary_limit: int = 6,
) -> list[list[str]]:
    outcome_terms = uniq(components.get("priority_outcomes", []))
    if len(outcome_terms) <= primary_limit:
        return []
    return chunk_terms(outcome_terms[primary_limit:], 4)[:4]


def _secondary_nutrition_chunks(
    components: dict[str, list[str]],
    *,
    primary_limit: int = 5,
) -> list[list[str]]:
    nutrition_terms = uniq(components.get("nutrition_terms", []))
    if len(nutrition_terms) <= primary_limit:
        return []
    return chunk_terms(nutrition_terms[primary_limit:], 4)[:4]


def _secondary_web_hint_chunks(
    components: dict[str, list[str]],
    *,
    primary_limit: int = 4,
) -> list[list[str]]:
    web_hint_terms = uniq(components.get("web_hints", []))
    if len(web_hint_terms) <= primary_limit:
        return []
    return chunk_terms(web_hint_terms[primary_limit:], 4)[:4]


def _secondary_focus_chunks(
    components: dict[str, list[str]],
    *,
    primary_limit: int = 5,
) -> list[list[str]]:
    focus_terms = uniq(components.get("focus_terms", []))
    if len(focus_terms) <= primary_limit:
        return []
    anchor_terms = {
        term.lower()
        for group_name in (
            "behavior_terms",
            "nutrition_terms",
            "diet_terms",
            "web_hints",
            "doc_type_terms",
        )
        for term in components.get(group_name, [])
    }
    overflow_terms = focus_terms[primary_limit:]
    focus_only_terms = [term for term in overflow_terms if term.lower() not in anchor_terms]
    prioritized_terms = uniq(focus_only_terms + overflow_terms)
    return chunk_terms(prioritized_terms, 4)[:6]


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


def _render_behavior_overflow_queries(
    components: dict[str, list[str]],
    provider: str,
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_behavior in _secondary_behavior_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_behavior, provider, 4),
                    _provider_or_block(condition_terms, provider, 6),
                    _provider_or_block(components["priority_outcomes"], provider, 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_behavior, provider, 4),
                    _provider_or_block(condition_terms, provider, 6),
                    _provider_or_block(components["doc_type_terms"], provider, 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_doc_type_overflow_queries(
    components: dict[str, list[str]],
    provider: str,
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_doc_types in _secondary_doc_type_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_doc_types, provider, 4),
                    _provider_or_block(condition_terms, provider, 6),
                    _provider_or_block(components["priority_outcomes"], provider, 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_doc_types, provider, 4),
                    _provider_or_block(components["web_hints"], provider, 4),
                    _provider_or_block(components["nutrition_terms"], provider, 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_outcome_overflow_queries(
    components: dict[str, list[str]],
    provider: str,
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_outcomes in _secondary_outcome_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(condition_terms, provider, 6),
                    _provider_or_block(extra_outcomes, provider, 4),
                    _provider_or_block(components["doc_type_terms"], provider, 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_outcomes, provider, 4),
                    _provider_or_block(components["diet_terms"], provider, 4),
                    _provider_or_block(components["behavior_terms"], provider, 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_nutrition_overflow_queries(
    components: dict[str, list[str]],
    provider: str,
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_nutrition in _secondary_nutrition_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_nutrition, provider, 4),
                    _provider_or_block(condition_terms, provider, 6),
                    _provider_or_block(components["doc_type_terms"], provider, 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_nutrition, provider, 4),
                    _provider_or_block(components["web_hints"], provider, 4),
                    _provider_or_block(components["behavior_terms"], provider, 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_web_hint_overflow_queries(
    components: dict[str, list[str]],
    provider: str,
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_web_hints in _secondary_web_hint_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_web_hints, provider, 4),
                    _provider_or_block(condition_terms, provider, 6),
                    _provider_or_block(components["doc_type_terms"], provider, 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_web_hints, provider, 4),
                    _provider_or_block(components["nutrition_terms"], provider, 4),
                    _provider_or_block(components["behavior_terms"], provider, 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_focus_overflow_queries(
    components: dict[str, list[str]],
    provider: str,
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_focus in _secondary_focus_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_focus, provider, 4),
                    _provider_or_block(condition_terms, provider, 6),
                    _provider_or_block(components["doc_type_terms"], provider, 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_focus, provider, 4),
                    _provider_or_block(condition_terms, provider, 6),
                    _provider_or_block(components["priority_outcomes"], provider, 4),
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


def _render_pubmed_behavior_overflow_queries(
    components: dict[str, list[str]],
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_behavior in _secondary_behavior_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_behavior, "pubmed", 4),
                    _provider_or_block(condition_terms, "pubmed", 6),
                    _provider_or_block(components["priority_outcomes"], "pubmed", 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_behavior, "pubmed", 4),
                    _provider_or_block(condition_terms, "pubmed", 6),
                    _pubmed_document_clause(components["doc_type_terms"]),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_pubmed_doc_type_overflow_queries(
    components: dict[str, list[str]],
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_doc_types in _secondary_doc_type_chunks(components):
        queries.append(
            _join_parts(
                [
                    _pubmed_document_clause(extra_doc_types),
                    _provider_or_block(condition_terms, "pubmed", 6),
                    _provider_or_block(components["priority_outcomes"], "pubmed", 4),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _pubmed_document_clause(extra_doc_types),
                    _provider_or_block(components["web_hints"], "pubmed", 4),
                    _provider_or_block(components["nutrition_terms"], "pubmed", 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_pubmed_outcome_overflow_queries(
    components: dict[str, list[str]],
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_outcomes in _secondary_outcome_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(condition_terms, "pubmed", 6),
                    _provider_or_block(extra_outcomes, "pubmed", 4),
                    _pubmed_document_clause(components["doc_type_terms"]),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_outcomes, "pubmed", 4),
                    _provider_or_block(components["diet_terms"], "pubmed", 4),
                    _provider_or_block(components["behavior_terms"], "pubmed", 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_pubmed_nutrition_overflow_queries(
    components: dict[str, list[str]],
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_nutrition in _secondary_nutrition_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_nutrition, "pubmed", 4),
                    _provider_or_block(condition_terms, "pubmed", 6),
                    _pubmed_document_clause(components["doc_type_terms"]),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_nutrition, "pubmed", 4),
                    _provider_or_block(components["web_hints"], "pubmed", 4),
                    _provider_or_block(components["behavior_terms"], "pubmed", 4),
                ]
            )
        )
    return uniq([query for query in queries if query])


def _render_pubmed_web_hint_overflow_queries(
    components: dict[str, list[str]],
) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    queries: list[str] = []
    for extra_web_hints in _secondary_web_hint_chunks(components):
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_web_hints, "pubmed", 4),
                    _provider_or_block(condition_terms, "pubmed", 6),
                    _pubmed_document_clause(components["doc_type_terms"]),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    _provider_or_block(extra_web_hints, "pubmed", 4),
                    _provider_or_block(components["nutrition_terms"], "pubmed", 4),
                    _provider_or_block(components["behavior_terms"], "pubmed", 4),
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
        + _render_pubmed_behavior_overflow_queries(components)
        + _render_pubmed_doc_type_overflow_queries(components)
        + _render_pubmed_outcome_overflow_queries(components)
        + _render_pubmed_nutrition_overflow_queries(components)
        + _render_pubmed_web_hint_overflow_queries(components)
        + _render_focus_overflow_queries(components, "pubmed")
        + _pubmed_mesh_expansion_queries(components)
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
                _provider_or_block(components["web_hints"], "europepmc", 4),
                _provider_or_block(components["nutrition_terms"], "europepmc", 5),
                _provider_or_block(condition_terms, "europepmc", 6),
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
        + _render_behavior_overflow_queries(components, "europepmc")
        + _render_doc_type_overflow_queries(components, "europepmc")
        + _render_outcome_overflow_queries(components, "europepmc")
        + _render_nutrition_overflow_queries(components, "europepmc")
        + _render_web_hint_overflow_queries(components, "europepmc")
        + _render_focus_overflow_queries(components, "europepmc")
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
                _provider_or_block(components["web_hints"], "openalex", 4),
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
        + _render_behavior_overflow_queries(components, "openalex")
        + _render_doc_type_overflow_queries(components, "openalex")
        + _render_outcome_overflow_queries(components, "openalex")
        + _render_nutrition_overflow_queries(components, "openalex")
        + _render_web_hint_overflow_queries(components, "openalex")
        + _render_focus_overflow_queries(components, "openalex")
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
        + _render_behavior_overflow_queries(components, "crossref")
        + _render_doc_type_overflow_queries(components, "crossref")
        + _render_outcome_overflow_queries(components, "crossref")
        + _render_nutrition_overflow_queries(components, "crossref")
        + _render_web_hint_overflow_queries(components, "crossref")
        + _render_focus_overflow_queries(components, "crossref")
    )


def _render_term_coverage_queries(components: dict[str, list[str]], provider: str) -> list[str]:
    condition_terms = components["condition_terms"] + components["clinical_terms"]
    outcome_terms = list(components.get("priority_outcomes", []))
    doc_terms = list(components.get("doc_type_terms", []))
    if provider == "pubmed":
        outcome_terms = [term for term in outcome_terms if str(term).lower() in {"glycemic control", "randomized controlled trial"}] + outcome_terms
        doc_terms = [term for term in doc_terms if str(term).lower() == "randomized controlled trial"] + doc_terms
    anchors = [
        _provider_or_block(condition_terms, provider, 6),
        _provider_or_block(outcome_terms, provider, 6)
        or _provider_or_block(doc_terms, provider, 6),
    ]
    terms = uniq(
        components.get("focus_terms", [])
        + components.get("web_hints", [])
        + components.get("behavior_terms", [])
        + components.get("nutrition_terms", [])
        + components.get("semantic_terms", [])
        + components.get("doc_type_terms", [])
    )
    queries: list[str] = []
    for term in terms:
        term_block = _provider_field_term(term, provider)
        if term_block:
            queries.append(_join_parts([term_block] + anchors))
    return uniq([query for query in queries if query])


_FOOD_ENVIRONMENT_PUBMED_TERMS = [
    "food environment intervention",
    "retail food environment",
    "healthy food retail",
    "healthy food procurement",
    "food procurement policy",
    "nutrition standards",
    "choice architecture",
    "healthy default",
    "menu labeling policy",
    "food policy implementation",
]

_EXTRA_PUBMED_TERMS: dict[str, list[str]] = {
    "busca2a": [
        "therapeutic lifestyle changes",
        "mediterranean dietary pattern",
        "dietary approaches to stop hypertension",
        "living guideline",
        "clinical guidance",
    ],
    "busca2b": [
        "medical nutrition therapy",
        "hybrid type 1",
        "hybrid type 2",
        "hybrid type 3",
        "steatotic liver disease",
        "metabolic dysfunction-associated steatohepatitis",
        "non-alcoholic fatty liver disease",
        "nonalcoholic steatohepatitis",
        "ketogenic diet",
        "low-carbohydrate diet",
        "low carbohydrate diet",
        "carbohydrate-restricted diet",
        "carbohydrate restricted diet",
        "network meta-analysis",
        "living systematic review",
        "rapid review",
        "food environment intervention",
        "food procurement policy",
        "healthy food retail",
        "choice architecture",
        "healthy default",
    ],
    "busca1": _FOOD_ENVIRONMENT_PUBMED_TERMS,
    "artigo3_framework": _FOOD_ENVIRONMENT_PUBMED_TERMS,
}


def _extra_pubmed_terms(workstream: str) -> list[str]:
    """Workstream-specific PubMed Title/Abstract terms folded into the querypack.

    These supplement the structured/semantic querypack with curated lifestyle
    nutrition and food-environment vocabulary. Kept inside the querypack (rather
    than an import-time runtime hook) so the search strategy is transparent and
    reproducible regardless of how the package is installed or invoked.
    """
    terms = _EXTRA_PUBMED_TERMS.get(canonical_workstream(workstream), [])
    return [f'"{term}"[Title/Abstract]' for term in terms]


def render_queries_for_provider(
    keyword_taxonomy: dict,
    workstream: str,
    provider: str,
    lexicon: dict | None = None,
) -> list[str]:
    _, components = build_structured_components(keyword_taxonomy, workstream)
    components = _augment_with_semantic_blocks(workstream, components)
    if provider == "pubmed":
        base = (
            _render_pubmed_queries(components)
            + _render_term_coverage_queries(components, "pubmed")
            + _extra_pubmed_terms(workstream)
        )
    elif provider in ("europepmc", "preprints"):
        # Preprints are served through Europe PMC (SRC:PPR) so they share its syntax.
        base = _render_europepmc_queries(components) + _render_term_coverage_queries(components, "europepmc")
    elif provider == "openalex":
        base = _render_openalex_queries(components) + _render_term_coverage_queries(components, "openalex")
    elif provider in ("crossref", "scielo"):
        # SciELO is served through Crossref (prefix filter) so it shares its syntax.
        base = _render_crossref_queries(components) + _render_term_coverage_queries(components, "crossref")
    elif provider in {"semantic_scholar", "doaj", "clinicaltrials", "core"}:
        # Generic keyword/boolean APIs.
        base = _render_crossref_queries(components) + _render_term_coverage_queries(components, provider)
    else:
        return []
    # Worldwide coverage: expand the workstream's concepts across many languages
    # (and language-independent MeSH for PubMed) so documents in any language are found.
    extra: list[str] = []
    if lexicon:
        extra = render_multilingual_queries(components, lexicon, provider)
        if provider == "pubmed":
            extra = extra + render_mesh_queries(components, lexicon)
    # Interleave so the multilingual/concept queries fall within the per-provider
    # query budget (which slices the prefix) instead of being appended past it.
    return uniq(_interleave_queries(base, extra))


def _interleave_queries(base: list[str], extra: list[str]) -> list[str]:
    """Weave the (smaller) extra list into base, front-loaded, ~2 base per extra."""
    if not extra:
        return base
    out: list[str] = []
    bi = ei = 0
    while bi < len(base) or ei < len(extra):
        if ei < len(extra):
            out.append(extra[ei])
            ei += 1
        for _ in range(2):
            if bi < len(base):
                out.append(base[bi])
                bi += 1
    return out


def build_provider_querypack(
    keyword_taxonomy: dict,
    workstreams: list[str],
    providers_by_workstream: dict[str, list[str]],
    lexicon: dict | None = None,
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
                lexicon=lexicon,
            )
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