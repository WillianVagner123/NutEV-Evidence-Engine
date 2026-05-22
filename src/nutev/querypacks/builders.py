from __future__ import annotations

from collections.abc import Iterable


WORKSTREAM_ALIASES = {
    "a3": "artigo3_framework",
    "article3": "artigo3_framework",
}

WORKSTREAM_QUERY_ENHANCEMENTS = {
    "busca1": {
        "focus_terms": [
            "medical nutrition therapy",
            "nutrition counseling",
            "nutrition counselling",
            "healthy eating pattern",
            "ultra-processed food",
            "meal planning",
            "shared meals",
            "commensality",
            "food is medicine",
            "produce prescription",
            "produce prescriptions",
            "medically tailored meals",
            "medically tailored groceries",
            "teaching kitchen",
        ],
        "web_hints": [
            "food-based dietary guideline",
            "dietary recommendation",
            "healthy diet",
            "nutrition policy",
            "guia alimentar",
            "food is medicine",
            "produce prescription",
            "medically tailored meals",
            "teaching kitchen",
        ],
        "document_terms": [
            "policy brief",
            "technical report",
            "practice recommendation",
        ],
    },
    "busca2a": {
        "condition_terms": [
            "dyslipidaemia",
            "hyperlipidemia",
            "hyperlipidaemia",
            "hypercholesterolemia",
            "hypercholesterolaemia",
            "lipid disorder",
            "lipid disorders",
            "atherogenic dyslipidemia",
            "atherogenic dyslipidaemia",
            "metabolic dysfunction-associated steatotic liver disease",
            "metabolic dysfunction associated steatotic liver disease",
            "steatotic liver disease",
        ],
        "focus_terms": [
            "medical nutrition therapy",
            "therapeutic lifestyle changes",
            "mediterranean dietary pattern",
            "dietary approaches to stop hypertension",
            "planetary health diet",
            "obesity management",
            "clinical nutrition",
            "cardiometabolic health",
            "glycemic control",
            "blood pressure",
            "fatty liver",
            "lipid management",
            "cholesterol management",
            "implementation strategy",
            "implementation strategies",
            "implementation outcome",
            "implementation outcomes",
            "implementation fidelity",
            "implementation determinant",
            "implementation determinants",
            "knowledge translation",
            "shared decision making",
            "practice facilitation",
        ],
        "web_hints": [
            "clinical practice guideline",
            "consensus statement",
            "scientific statement",
            "obesity guideline",
            "cardiometabolic guideline",
            "dyslipidemia guideline",
            "lipid management guideline",
        ],
        "document_terms": [
            "consensus statement",
            "scientific statement",
            "clinical pathway",
        ],
    },
    "busca2b": {
        "condition_terms": [
            "dyslipidaemia",
            "hyperlipidemia",
            "hyperlipidaemia",
            "hypercholesterolemia",
            "hypercholesterolaemia",
            "lipid disorder",
            "lipid disorders",
            "atherogenic dyslipidemia",
            "atherogenic dyslipidaemia",
            "metabolic dysfunction-associated steatotic liver disease",
            "metabolic dysfunction associated steatotic liver disease",
            "steatotic liver disease",
            "masld",
            "mafld",
            "nafld",
            "mash",
            "nash",
            "nonalcoholic fatty liver disease",
            "non-alcoholic fatty liver disease",
            "nonalcoholic steatohepatitis",
            "non-alcoholic steatohepatitis",
            "metabolic dysfunction-associated fatty liver disease",
            "metabolic dysfunction associated fatty liver disease",
            "fatty liver",
        ],
        "focus_terms": [
            "medical nutrition therapy",
            "therapeutic lifestyle changes",
            "mediterranean dietary pattern",
            "dietary approaches to stop hypertension",
            "planetary health diet",
            "registered dietitian",
            "registered dietitian nutritionist",
            "dietitian-led intervention",
            "dietitian led intervention",
            "lifestyle intervention",
            "behavioral intervention",
            "nutrition counseling",
            "nutrition counselling",
            "meal replacement",
            "time-restricted eating",
            "intermittent fasting",
            "diabetes prevention program",
            "weight maintenance",
            "lipid management",
            "cholesterol management",
            "shared decision making",
            "implementation strategy",
            "implementation strategies",
            "implementation outcome",
            "implementation outcomes",
            "implementation fidelity",
            "implementation determinant",
            "implementation determinants",
            "implementation barriers",
            "implementation facilitators",
            "practice facilitation",
            "knowledge translation",
            "food is medicine",
            "produce prescription",
            "produce prescriptions",
            "medically tailored meals",
            "medically tailored groceries",
            "teaching kitchen",
        ],
        "web_hints": [
            "randomized trial",
            "systematic review",
            "implementation study",
            "adherence intervention",
            "behavior change trial",
            "dyslipidemia trial",
            "lipid lowering trial",
            "masld trial",
            "nafld trial",
            "steatotic liver disease trial",
            "network meta-analysis",
            "umbrella review",
            "overview of reviews",
            "review of reviews",
            "implementation determinants",
            "implementation barriers",
            "implementation facilitators",
            "food is medicine intervention",
            "produce prescription program",
            "medically tailored meals",
            "teaching kitchen",
        ],
        "document_terms": [
            "randomized trial",
            "systematic review",
            "meta-analysis",
            "network meta-analysis",
            "umbrella review",
        ],
    },
    "artigo3_framework": {
        "focus_terms": [
            "nutrition literacy",
            "food agency",
            "psychometric validation",
            "scale development",
            "questionnaire validation",
            "implementation framework",
            "self-efficacy",
            "cooking skills",
        ],
        "web_hints": [
            "questionnaire validation",
            "survey instrument",
            "framework development",
            "food literacy scale",
            "psychometric study",
        ],
        "document_terms": [
            "framework",
            "questionnaire",
            "validation study",
        ],
    },
}

DOWNLOAD_QUERY_GROUPS = {
    "default": [
        ["filetype:pdf"],
        ["pdf", "download", "full text"],
        ["open access", "free full text", "PMC"],
    ],
    "busca1": [
        ["filetype:pdf", "guideline", "report"],
        ["manual", "toolkit", "technical report"],
    ],
    "busca2a": [
        ["filetype:pdf", "clinical practice guideline"],
        ["consensus statement", "scientific statement", "PDF"],
    ],
    "busca2b": [
        ["filetype:pdf", "randomized controlled trial"],
        ["supplement", "protocol", "full text"],
    ],
    "artigo3_framework": [
        ["filetype:pdf", "questionnaire", "instrument"],
        ["scale development", "psychometric", "appendix"],
    ],
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


def _search_term(term: str) -> str:
    clean = str(term).strip()
    if not clean:
        return ""
    if clean.lower().startswith(("filetype:", "site:")):
        return clean
    return quote_term(clean)


def search_or_block(terms: list[str], limit: int | None = None) -> str:
    chunk = uniq(terms)
    if limit is not None:
        chunk = chunk[:limit]
    chunk = [_search_term(term) for term in chunk if term]
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


def chunk_terms(terms: list[str], chunk_size: int = 5) -> list[list[str]]:
    clean = uniq(terms)
    return [clean[i : i + chunk_size] for i in range(0, len(clean), chunk_size)]


def build_structured_components(
    keyword_taxonomy: dict,
    workstream: str,
) -> tuple[str, dict[str, list[str]]]:
    ws_key = canonical_workstream(workstream)
    ws = keyword_taxonomy.get("workstreams", {}).get(ws_key, {})
    global_cfg = keyword_taxonomy.get("global", {})
    clinical_cfg = keyword_taxonomy.get("clinical", {})
    outcomes_cfg = keyword_taxonomy.get("outcomes", {})
    enhancements = WORKSTREAM_QUERY_ENHANCEMENTS.get(ws_key, {})

    population_terms = uniq(ws.get("population_terms", []))
    condition_terms = uniq(
        ws.get("condition_terms", []) + enhancements.get("condition_terms", [])
    )
    clinical_terms = get_named_terms(clinical_cfg, ws.get("clinical_keys", []))
    priority_outcomes = uniq(
        get_named_terms(outcomes_cfg, ws.get("priority_outcomes", []))
        + enhancements.get("priority_outcomes", [])
    )
    doc_type_terms = get_named_terms(
        global_cfg.get("document_types", {}),
        ws.get("document_type_keys", []),
    )
    doc_type_terms = uniq(doc_type_terms + enhancements.get("document_terms", []))
    web_hints = uniq(
        ws.get("web_query_hints", []) + enhancements.get("web_hints", [])
    )
    behavior_terms = get_global_block(keyword_taxonomy, "implementation_behavior")
    diet_terms = get_global_block(keyword_taxonomy, "diet_patterns")
    nutrition_terms = get_global_block(keyword_taxonomy, "nutrition_domains")

    focus_terms: list[str] = []
    for block_name in ws.get("focus_blocks", []):
        focus_terms.extend(get_global_block(keyword_taxonomy, block_name))
    focus_terms = uniq(focus_terms + enhancements.get("focus_terms", []))

    return ws_key, {
        "population_terms": population_terms,
        "condition_terms": condition_terms,
        "clinical_terms": clinical_terms,
        "priority_outcomes": priority_outcomes,
        "doc_type_terms": doc_type_terms,
        "web_hints": web_hints,
        "behavior_terms": behavior_terms,
        "diet_terms": diet_terms,
        "nutrition_terms": nutrition_terms,
        "focus_terms": focus_terms,
    }


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


def _add_capture_queries(
    queries: list[str],
    ws_key: str,
    condition_terms: list[str],
    clinical_terms: list[str],
    focus_terms: list[str],
    priority_outcomes: list[str],
    doc_type_terms: list[str],
    web_hints: list[str],
) -> None:
    condition_block = or_block(condition_terms + clinical_terms, 8)
    seed_queries = [
        _join_parts(
            [
                or_block(web_hints, 4),
                condition_block,
                or_block(doc_type_terms, 4),
            ]
        ),
        _join_parts(
            [
                or_block(focus_terms, 5),
                or_block(doc_type_terms, 5),
                or_block(priority_outcomes, 4),
            ]
        ),
        _join_parts(
            [
                condition_block,
                or_block(focus_terms, 4),
                or_block(web_hints + doc_type_terms, 5),
            ]
        ),
    ]
    qualifier_groups = uniq_nested(
        DOWNLOAD_QUERY_GROUPS.get(ws_key, []) + DOWNLOAD_QUERY_GROUPS["default"]
    )

    for seed in seed_queries:
        if not seed:
            continue
        for qualifiers in qualifier_groups[:5]:
            queries.append(_join_parts([seed, search_or_block(qualifiers, 4)]))


def uniq_nested(groups: list[list[str]]) -> list[list[str]]:
    seen = set()
    output = []
    for group in groups:
        clean = uniq(group)
        key = tuple(term.lower() for term in clean)
        if not clean or key in seen:
            continue
        seen.add(key)
        output.append(clean)
    return output


def _add_specific_busca1(
    queries,
    population_terms,
    condition_terms,
    nutrition_terms,
    behavior_terms,
    diet_terms,
):
    guideline_terms = [
        "food-based dietary guideline",
        "food based dietary guidelines",
        "dietary guideline",
        "dietary guidelines",
        "food guide",
        "nutrition guideline",
        "guia alimentar",
        "diretrizes alimentares",
        "guia de alimentação",
        "healthy eating recommendation",
    ]
    grey_terms = [
        "technical report",
        "policy brief",
        "white paper",
        "manual",
        "framework",
        "report",
        "toolkit",
        "relatório técnico",
        "nota técnica",
        "manual",
        "relatório",
    ]
    queries.append(
        _join_parts(
            [
                or_block(population_terms, 5),
                or_block(condition_terms, 6),
                or_block(guideline_terms, 6),
            ]
        )
    )
    queries.append(
        _join_parts(
            [
                or_block(condition_terms, 6),
                or_block(grey_terms, 6),
                or_block(nutrition_terms, 6),
            ]
        )
    )
    queries.append(
        _join_parts(
            [
                or_block(condition_terms, 6),
                or_block(diet_terms, 6),
                or_block(behavior_terms, 6),
            ]
        )
    )


def _add_specific_busca2a(
    queries,
    condition_terms,
    clinical_terms,
    outcome_terms,
    diet_terms,
):
    guideline_terms = [
        "guideline",
        "guidelines",
        "clinical practice guideline",
        "practice guideline",
        "guidance",
        "scientific statement",
        "statement",
        "consensus",
        "position statement",
        "diretriz",
        "diretrizes",
        "consenso",
        "declaração científica",
        "recomendação",
    ]
    clinical_chunks = chunk_terms(condition_terms + clinical_terms, 4)
    outcome_chunks = chunk_terms(outcome_terms, 5)

    for c in clinical_chunks[:10]:
        queries.append(
            _join_parts(
                [or_block(c), or_block(guideline_terms, 6), or_block(outcome_terms, 6)]
            )
        )

    for o in outcome_chunks[:8]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(o),
                    or_block(guideline_terms, 6),
                ]
            )
        )

    for d in chunk_terms(diet_terms, 4)[:6]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(d),
                    or_block(guideline_terms, 6),
                ]
            )
        )


def _add_specific_busca2b(
    queries,
    condition_terms,
    clinical_terms,
    outcome_terms,
    behavior_terms,
    diet_terms,
):
    trial_terms = [
        "randomized controlled trial",
        "controlled trial",
        "pragmatic trial",
        "pilot study",
        "feasibility study",
        "ensaio clínico randomizado",
        "ensaio controlado",
        "estudo piloto",
        "estudo de viabilidade",
    ]
    review_terms = [
        "systematic review",
        "scoping review",
        "integrative review",
        "umbrella review",
        "meta-analysis",
        "network meta-analysis",
        "network meta analysis",
        "rapid review",
        "living systematic review",
        "overview of reviews",
        "review of reviews",
        "revisão sistemática",
        "revisão de escopo",
        "revisão integrativa",
        "metanálise",
    ]
    hepatic_terms = [
        "masld",
        "mafld",
        "nafld",
        "mash",
        "nash",
        "steatotic liver disease",
        "fatty liver",
        "nonalcoholic fatty liver disease",
        "non-alcoholic fatty liver disease",
        "nonalcoholic steatohepatitis",
        "non-alcoholic steatohepatitis",
        "metabolic dysfunction-associated fatty liver disease",
        "metabolic dysfunction associated fatty liver disease",
        "metabolic dysfunction-associated steatotic liver disease",
        "metabolic dysfunction associated steatotic liver disease",
    ]

    for d in chunk_terms(diet_terms, 4)[:12]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(d),
                    or_block(trial_terms, 6),
                    or_block(outcome_terms, 5),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(d),
                    or_block(review_terms, 6),
                    or_block(outcome_terms, 5),
                ]
            )
        )

    for b in chunk_terms(behavior_terms, 5)[:8]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(b),
                    or_block(trial_terms, 6),
                    or_block(outcome_terms, 5),
                ]
            )
        )

    for hepatic_chunk in chunk_terms(hepatic_terms, 4)[:6]:
        queries.append(
            _join_parts(
                [
                    or_block(hepatic_chunk),
                    or_block(diet_terms, 5),
                    or_block(trial_terms, 5),
                    or_block(outcome_terms, 5),
                ]
            )
        )
        queries.append(
            _join_parts(
                [
                    or_block(hepatic_chunk),
                    or_block(behavior_terms, 5),
                    or_block(review_terms, 5),
                    or_block(outcome_terms, 5),
                ]
            )
        )


def _add_specific_a3(
    queries,
    condition_terms,
    clinical_terms,
    behavior_terms,
    diet_terms,
):
    instrument_terms = [
        "framework",
        "questionnaire",
        "instrument",
        "index",
        "food literacy instrument",
        "culinary skills instrument",
        "commensality",
        "questionário",
        "índice",
    ]
    competence_terms = [
        "food literacy",
        "culinary medicine",
        "cooking skills",
        "meal planning",
        "shared meals",
        "commensality",
        "behavior change",
        "self-monitoring",
        "literacia alimentar",
        "habilidades culinárias",
        "planejamento de refeições",
    ]
    review_terms = [
        "systematic review",
        "scoping review",
        "integrative review",
        "umbrella review",
        "meta-analysis",
        "network meta-analysis",
        "network meta analysis",
        "rapid review",
        "living systematic review",
        "overview of reviews",
        "review of reviews",
    ]

    queries.append(
        _join_parts([or_block(instrument_terms, 8), or_block(competence_terms, 8)])
    )
    queries.append(
        _join_parts(
            [
                or_block(condition_terms + clinical_terms, 8),
                or_block(instrument_terms, 8),
                or_block(behavior_terms, 6),
            ]
        )
    )
    queries.append(
        _join_parts(
            [
                or_block(diet_terms, 6),
                or_block(instrument_terms, 8),
                or_block(behavior_terms, 6),
            ]
        )
    )
    queries.append(
        _join_parts(
            [
                or_block(instrument_terms, 8),
                or_block(competence_terms, 8),
                or_block(review_terms, 6),
            ]
        )
    )


def build_queries(keyword_taxonomy: dict, workstream: str) -> list[str]:
    ws_key = canonical_workstream(workstream)
    ws = keyword_taxonomy.get("workstreams", {}).get(ws_key, {})
    if not ws:
        return []

    if ws.get("base_terms") and ws.get("themes"):
        return _build_legacy_queries(ws)

    ws_key, components = build_structured_components(keyword_taxonomy, workstream)
    population_terms = components["population_terms"]
    condition_terms = components["condition_terms"]
    clinical_terms = components["clinical_terms"]
    priority_outcomes = components["priority_outcomes"]
    doc_type_terms = components["doc_type_terms"]
    web_hints = components["web_hints"]
    behavior_terms = components["behavior_terms"]
    diet_terms = components["diet_terms"]
    nutrition_terms = components["nutrition_terms"]
    focus_terms = components["focus_terms"]

    queries: list[str] = []

    queries.append(
        _join_parts(
            [
                or_block(population_terms, 6),
                or_block(condition_terms + clinical_terms, 8),
                or_block(doc_type_terms, 6),
            ]
        )
    )
    queries.append(
        _join_parts(
            [
                or_block(condition_terms + clinical_terms, 8),
                or_block(priority_outcomes, 6),
                or_block(doc_type_terms, 6),
            ]
        )
    )
    queries.append(
        _join_parts(
            [
                or_block(web_hints, 5),
                or_block(condition_terms + clinical_terms, 8),
            ]
        )
    )

    for chunk in chunk_terms(focus_terms, 5)[:16]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(chunk, 5),
                    or_block(doc_type_terms, 6),
                ]
            )
        )

    for outcome_chunk in chunk_terms(priority_outcomes, 5)[:8]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(outcome_chunk, 5),
                ]
            )
        )

    for behavior_chunk in chunk_terms(behavior_terms, 5)[:8]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(priority_outcomes, 5),
                    or_block(behavior_chunk, 5),
                ]
            )
        )

    for diet_chunk in chunk_terms(diet_terms, 4)[:10]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(diet_chunk, 4),
                    or_block(priority_outcomes, 5),
                ]
            )
        )

    for nutrition_chunk in chunk_terms(nutrition_terms, 5)[:8]:
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(nutrition_chunk, 5),
                    or_block(behavior_terms, 5),
                ]
            )
        )

    for hint_chunk in chunk_terms(web_hints, 4)[:8]:
        queries.append(
            _join_parts(
                [
                    or_block(hint_chunk, 4),
                    or_block(focus_terms, 5),
                    or_block(doc_type_terms, 5),
                ]
            )
        )

    _add_capture_queries(
        queries,
        ws_key,
        condition_terms,
        clinical_terms,
        focus_terms,
        priority_outcomes,
        doc_type_terms,
        web_hints,
    )

    if ws_key == "busca1":
        _add_specific_busca1(
            queries,
            population_terms,
            condition_terms,
            nutrition_terms,
            behavior_terms,
            diet_terms,
        )
    elif ws_key == "busca2a":
        _add_specific_busca2a(
            queries,
            condition_terms,
            clinical_terms,
            priority_outcomes,
            diet_terms,
        )
    elif ws_key == "busca2b":
        _add_specific_busca2b(
            queries,
            condition_terms,
            clinical_terms,
            priority_outcomes,
            behavior_terms,
            diet_terms,
        )
    elif ws_key == "artigo3_framework":
        _add_specific_a3(
            queries,
            condition_terms,
            clinical_terms,
            behavior_terms,
            diet_terms,
        )

    return uniq([q for q in queries if q])


def build_querypack(
    keyword_taxonomy: dict,
    workstreams: Iterable[str],
) -> dict[str, list[str]]:
    return {ws: build_queries(keyword_taxonomy, ws) for ws in workstreams}
