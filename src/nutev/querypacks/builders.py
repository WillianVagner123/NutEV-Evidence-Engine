from __future__ import annotations

from collections.abc import Iterable


WORKSTREAM_ALIASES = {
    "a3": "artigo3_framework",
    "article3": "artigo3_framework",
    # Canonical article renumbering (P5): the behavioural framework is Article 4.
    "a4": "artigo3_framework",
    "a4_framework": "artigo3_framework",
}

BEHAVIOR_CHANGE_PLANNING_TERMS = [
    "action planning",
    "coping planning",
    "self-regulation",
    "self regulation",
    "readiness to change",
    "stage of change",
    "stages of change",
    "transtheoretical model",
]

NUTRITION_CARE_PATHWAY_TERMS = [
    "medical nutrition therapy",
    "nutrition care process",
    "nutrition care process model",
    "nutrition care pathway",
    "nutrition care pathways",
    "nutrition care protocol",
    "nutrition care protocols",
]

DIETITIAN_IMPLEMENTATION_TERMS = [
    "dietitian-delivered intervention",
    "dietitian delivered intervention",
    "dietitian-managed intervention",
    "dietitian managed intervention",
    "registered dietitian-led intervention",
    "registered dietitian led intervention",
    "registered dietitian nutritionist-led intervention",
    "registered dietitian nutritionist led intervention",
]

BROAD_LIFESTYLE_TERMS_REQUIRING_NUTRITION_ANCHOR = {
    "lifestyle medicine",
    "medicina do estilo de vida",
    "lifestyle intervention",
    "lifestyle modification",
    "therapeutic lifestyle changes",
    "therapeutic lifestyle change",
    "healthy lifestyle",
    "estilo de vida saudável",
    "physical activity",
    "exercise",
    "movement",
    "atividade física",
    "exercício",
    "sedentary",
    "sedentário",
    "sleep",
    "sleep quality",
    "circadian",
    "stress",
    "mindfulness",
    "social connection",
    "social support",
    "sono",
    "qualidade do sono",
    "ritmo circadiano",
    "estresse",
    "atenção plena",
    "conexões sociais",
    "suporte social",
    "smoking cessation",
    "alcohol",
    "substance use",
    "tabaco",
    "tabagismo",
    "álcool",
}

NUTRITION_ANCHOR_FALLBACK_TERMS = [
    "nutrition",
    "nutrição",
    "diet",
    "dietary",
    "food",
    "healthy eating",
    "dietary pattern",
    "medical nutrition therapy",
]

SOCIAL_PRESCRIBING_ACCESS_TERMS = [
    "social prescribing",
    "social prescribing program",
    "social prescribing programme",
    "social prescribing link worker",
    "link worker",
    "link workers",
    "community connector",
    "community connectors",
    "social needs referral",
    "social needs intervention",
    "screening and referral",
    "closed-loop referral",
    "closed loop referral",
    "community referral",
    "community referrals",
    "community resource referral",
    "community resource referrals",
    "food pantry referral",
    "food pantry referral program",
    "food bank partnership",
    "community food program",
    "community food programme",
    "community health worker-led nutrition",
    "community health worker led nutrition",
    "patient navigation",
    "care navigation",
    "food pharmacy",
    "food pharmacy program",
    "food pharmacy programme",
    "food is medicine referral",
    "food as medicine referral",
    "produce prescription referral",
    "medically tailored food referral",
    "nutrition security referral",
]

ADVANCED_DYSLIPIDEMIA_TERMS = [
    "hypertriglyceridemia",
    "hypertriglyceridaemia",
    "atherogenic dyslipidemia",
    "atherogenic dyslipidaemia",
    "remnant cholesterol",
    "triglyceride-rich lipoprotein",
    "triglyceride rich lipoprotein",
    "apolipoprotein b",
    "apo b",
    "non-hdl cholesterol",
    "non hdl cholesterol",
]

CARDIOMETABOLIC_PRECISION_TERMS = [
    "cardiometabolic risk",
    "cardiometabolic health",
    "cardiometabolic disease",
    "cardiometabolic diseases",
    "metabolic syndrome",
    "metabolic syndrome x",
    "insulin resistance",
    "central adiposity",
    "abdominal adiposity",
    "visceral adiposity",
    "waist circumference",
    "waist-to-height ratio",
    "waist to height ratio",
    "waist-to-hip ratio",
    "waist to hip ratio",
]

ADVANCED_DYSLIPIDEMIA_FOCUS_TERMS = ADVANCED_DYSLIPIDEMIA_TERMS + [
    "lipid lowering",
    "triglyceride lowering",
    "apo b management",
    "apolipoprotein b management",
    "remnant cholesterol management",
]

METABOLIC_REMISSION_TERMS = [
    "diabetes remission",
    "type 2 diabetes remission",
    "diabetes reversal",
    "glycemic remission",
    "glycaemic remission",
    "remission of type 2 diabetes",
    "weight loss maintenance",
    "long-term weight loss maintenance",
    "long term weight loss maintenance",
    "weight regain prevention",
    "weight regain management",
]

METABOLIC_REMISSION_WEB_HINTS = [
    "diabetes remission guideline",
    "diabetes remission consensus",
    "diabetes remission consensus report",
    "type 2 diabetes remission guideline",
    "type 2 diabetes remission consensus",
    "weight loss maintenance trial",
    "weight loss maintenance systematic review",
    "weight regain prevention trial",
]

METABOLIC_REMISSION_DOCUMENT_TERMS = [
    "remission consensus",
    "remission consensus report",
    "remission guideline",
    "weight loss maintenance trial",
    "weight loss maintenance systematic review",
]

EXPANDED_GUIDELINE_VARIANTS = [
    "nutrition practice guideline",
    "dietetic practice guideline",
    "practice advisory",
    "policy statement",
    "consensus update",
    "guideline update",
    "clinical practice update",
    "best practice advice",
    "joint statement",
    "joint guideline",
    "living guideline",
    "clinical pathway",
    "care pathway",
    "clinical decision pathway",
    "decision pathway",
    "clinical practice recommendation",
    "clinical practice recommendations",
    "scientific advisory",
]

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
            "food as medicine",
            "food as medicine intervention",
            "produce prescription",
            "produce prescriptions",
            "produce prescription program",
            "food prescription program",
            "healthy food prescription",
            "healthy food incentive",
            "healthy food incentives",
            "nutrition incentive",
            "nutrition incentives",
            "produce voucher",
            "produce vouchers",
            "fruit and vegetable voucher",
            "fruit and vegetable vouchers",
            "medically tailored meal",
            "medically tailored meals",
            "medically tailored grocery",
            "medically tailored groceries",
            "medically tailored pantry",
            "medically tailored pantries",
            "medically tailored food package",
            "medically tailored food packages",
            "teaching kitchen",
        ],
        "web_hints": [
            "food is medicine",
            "food as medicine",
            "produce prescription program",
            "food prescription program",
            "healthy food prescription",
            "healthy food incentive",
            "healthy food incentives",
            "nutrition incentive",
            "nutrition incentives",
            "produce voucher",
            "produce vouchers",
            "fruit and vegetable voucher",
            "fruit and vegetable vouchers",
            "medically tailored pantry",
            "medically tailored pantries",
            "medically tailored food package",
            "medically tailored food packages",
            "food-based dietary guideline",
            "dietary recommendation",
            "healthy diet",
            "nutrition policy",
            "guia alimentar",
            "medically tailored meal",
            "medically tailored meals",
            "medically tailored grocery",
            "medically tailored groceries",
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
            "prediabetes",
            "pre-diabetes",
            "prediabetic state",
            "impaired fasting glucose",
            "impaired glucose tolerance",
            "dysglycemia",
            "dysglycaemia",
            "glucose intolerance",
            "insulin resistance",
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
            "metabolic dysfunction-associated steatohepatitis",
            "metabolic dysfunction associated steatohepatitis",
            "fatty liver",
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
            "prediabetes",
            "pre-diabetes",
            "prediabetic state",
            "impaired fasting glucose",
            "impaired glucose tolerance",
            "dysglycemia",
            "dysglycaemia",
            "glucose intolerance",
            "insulin resistance",
            "glycemic control",
            "blood pressure",
            "fatty liver",
            "lipid management",
            "cholesterol management",
        ],
        "web_hints": [
            "clinical practice guideline",
            "consensus statement",
            "scientific statement",
            "obesity guideline",
            "cardiometabolic guideline",
            "prediabetes guideline",
            "pre-diabetes guideline",
            "prediabetic state guideline",
            "impaired fasting glucose guideline",
            "impaired glucose tolerance guideline",
            "insulin resistance guideline",
            "dyslipidemia guideline",
            "lipid management guideline",
            "practice guidance",
            "guidance statement",
            "best practice advice",
            "clinical decision pathway",
            "consensus guidance",
            "clinical practice recommendations",
            "scientific advisory",
            "standards of care",
            "standards of medical care in diabetes",
            "consensus report",
        ],
        "document_terms": [
            "consensus statement",
            "scientific statement",
            "clinical pathway",
            "practice guidance",
            "guidance statement",
            "best practice advice",
            "clinical decision pathway",
            "consensus guidance",
            "clinical practice recommendations",
            "scientific advisory",
            "standards of care",
            "standards of medical care in diabetes",
            "consensus report",
        ],
    },
    "busca2b": {
        "condition_terms": [
            "prediabetes",
            "pre-diabetes",
            "prediabetic state",
            "impaired fasting glucose",
            "impaired glucose tolerance",
            "dysglycemia",
            "dysglycaemia",
            "glucose intolerance",
            "insulin resistance",
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
            "metabolic dysfunction-associated steatohepatitis",
            "metabolic dysfunction associated steatohepatitis",
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
            "intensive lifestyle intervention",
            "lifestyle program",
            "lifestyle programme",
            "behavioral intervention",
            "action planning",
            "coping planning",
            "self-regulation",
            "self regulation",
            "readiness to change",
            "stage of change",
            "stages of change",
            "transtheoretical model",
            "nutrition counseling",
            "nutrition counselling",
            "meal replacement",
            "time-restricted eating",
            "intermittent fasting",
            "diabetes prevention program",
            "prediabetes",
            "pre-diabetes",
            "prediabetic state",
            "impaired fasting glucose",
            "impaired glucose tolerance",
            "dysglycemia",
            "dysglycaemia",
            "glucose intolerance",
            "insulin resistance",
            "weight maintenance",
            "lipid management",
            "cholesterol management",
            "shared decision making",
            "implementation determinants",
            "implementation barriers",
            "implementation facilitators",
            "implementation framework",
            "implementation frameworks",
            "implementation strategy",
            "implementation strategies",
            "implementation outcomes",
            "implementation climate",
            "organizational readiness",
            "readiness for implementation",
            "penetration",
            "sustainment",
            "implementation trial",
            "implementation evaluation",
            "process evaluation",
            "quality improvement",
            "quality improvement study",
            "real-world implementation",
            "real world implementation",
            "real-world evidence",
            "real world evidence",
            "scale-up",
            "scale up",
            "scale-out",
            "scale out",
            "audit and feedback",
            "service delivery",
            "care delivery",
            "program implementation",
            "hybrid effectiveness-implementation",
            "hybrid effectiveness implementation",
            "consolidated framework for implementation research",
            "cfir",
            "re-aim",
            "normalization process theory",
            "theoretical domains framework",
            "practice facilitation",
            "food is medicine",
            "food as medicine",
            "food as medicine intervention",
            "produce prescription",
            "produce prescriptions",
            "produce prescription program",
            "food prescription program",
            "healthy food prescription",
            "healthy food incentive",
            "healthy food incentives",
            "nutrition incentive",
            "nutrition incentives",
            "produce voucher",
            "produce vouchers",
            "fruit and vegetable voucher",
            "fruit and vegetable vouchers",
            "medically tailored meal",
            "medically tailored meals",
            "medically tailored grocery",
            "medically tailored groceries",
            "medically tailored pantry",
            "medically tailored pantries",
            "medically tailored food package",
            "medically tailored food packages",
            "teaching kitchen",
        ],
        "web_hints": [
            "food is medicine",
            "food as medicine",
            "food is medicine intervention",
            "produce prescription program",
            "food prescription program",
            "healthy food prescription",
            "healthy food incentive",
            "healthy food incentives",
            "nutrition incentive",
            "nutrition incentives",
            "produce voucher",
            "produce vouchers",
            "fruit and vegetable voucher",
            "fruit and vegetable vouchers",
            "medically tailored pantry",
            "medically tailored pantries",
            "medically tailored food package",
            "medically tailored food packages",
            "randomized trial",
            "systematic review",
            "implementation study",
            "implementation trial",
            "implementation evaluation",
            "process evaluation",
            "quality improvement",
            "quality improvement study",
            "action planning",
            "coping planning",
            "self-regulation",
            "readiness to change",
            "stages of change",
            "transtheoretical model",
            "implementation climate",
            "organizational readiness",
            "readiness for implementation",
            "penetration",
            "sustainment",
            "real-world implementation",
            "real world implementation",
            "real-world evidence",
            "real world evidence",
            "scale-up",
            "scale up",
            "scale-out",
            "scale out",
            "audit and feedback",
            "service delivery",
            "care delivery",
            "program implementation",
            "adherence intervention",
            "behavior change trial",
            "prediabetes trial",
            "pre-diabetes trial",
            "prediabetic state trial",
            "impaired fasting glucose trial",
            "impaired glucose tolerance trial",
            "insulin resistance trial",
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
            "implementation framework",
            "hybrid effectiveness-implementation",
            "consolidated framework for implementation research",
            "cfir",
            "re-aim",
            "normalization process theory",
            "medically tailored meal",
            "medically tailored meals",
            "medically tailored grocery",
            "medically tailored groceries",
            "teaching kitchen",
            "intensive lifestyle intervention",
            "lifestyle program",
            "lifestyle programme",
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
            "implementation frameworks",
            "implementation strategy",
            "implementation strategies",
            "implementation outcomes",
            "action planning",
            "coping planning",
            "self-regulation",
            "self regulation",
            "readiness to change",
            "stage of change",
            "stages of change",
            "transtheoretical model",
            "hybrid effectiveness-implementation",
            "hybrid effectiveness implementation",
            "consolidated framework for implementation research",
            "cfir",
            "re-aim",
            "normalization process theory",
            "theoretical domains framework",
            "self-efficacy",
            "cooking skills",
        ],
        "web_hints": [
            "questionnaire validation",
            "survey instrument",
            "framework development",
            "food literacy scale",
            "psychometric study",
            "action planning",
            "coping planning",
            "self-regulation",
            "readiness to change",
            "stages of change",
            "transtheoretical model",
            "implementation framework",
            "hybrid effectiveness-implementation",
            "consolidated framework for implementation research",
            "cfir",
            "re-aim",
            "normalization process theory",
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


def _needs_nutrition_anchor(terms: list[str]) -> bool:
    return any(
        term.lower() in BROAD_LIFESTYLE_TERMS_REQUIRING_NUTRITION_ANCHOR
        for term in terms
    )


def _nutrition_anchor_terms(
    nutrition_terms: list[str],
    diet_terms: list[str],
) -> list[str]:
    prioritized_terms = [
        "medical nutrition therapy",
        "nutrition counseling",
        "nutrition counselling",
        "dietary counseling",
        "dietary counselling",
        "dietary pattern",
        "dietary patterns",
        "healthy diet",
        "healthy eating",
        "food literacy",
        "culinary medicine",
        "meal planning",
    ]
    available_terms = nutrition_terms + diet_terms + NUTRITION_ANCHOR_FALLBACK_TERMS
    prioritized = [term for term in prioritized_terms if term.lower() in {t.lower() for t in available_terms}]
    return uniq(prioritized + available_terms)


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
    if ws_key in {"busca2a", "busca2b"}:
        condition_terms = uniq(
            condition_terms + ADVANCED_DYSLIPIDEMIA_TERMS + CARDIOMETABOLIC_PRECISION_TERMS
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
    if "guidelines" in ws.get("document_type_keys", []):
        doc_type_terms = uniq(EXPANDED_GUIDELINE_VARIANTS + doc_type_terms)
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
    if ws_key in {"busca2a", "busca2b"}:
        focus_terms = uniq(
            focus_terms
            + ADVANCED_DYSLIPIDEMIA_FOCUS_TERMS
            + CARDIOMETABOLIC_PRECISION_TERMS
            + METABOLIC_REMISSION_TERMS
        )
        priority_outcomes = uniq(
            priority_outcomes + CARDIOMETABOLIC_PRECISION_TERMS + METABOLIC_REMISSION_TERMS
        )
        doc_type_terms = uniq(doc_type_terms + METABOLIC_REMISSION_DOCUMENT_TERMS)

    if ws_key in {"busca2a", "busca2b"}:
        focus_terms = uniq(focus_terms + NUTRITION_CARE_PATHWAY_TERMS)
        web_hints = uniq(
            web_hints + NUTRITION_CARE_PATHWAY_TERMS + METABOLIC_REMISSION_WEB_HINTS
        )
    if ws_key in {"busca1", "busca2b"}:
        focus_terms = uniq(focus_terms + SOCIAL_PRESCRIBING_ACCESS_TERMS)
        web_hints = uniq(web_hints + SOCIAL_PRESCRIBING_ACCESS_TERMS)
    if ws_key == "busca2b":
        focus_terms = uniq(focus_terms + DIETITIAN_IMPLEMENTATION_TERMS)
        web_hints = uniq(web_hints + DIETITIAN_IMPLEMENTATION_TERMS)

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
    nutrition_anchor_terms = _nutrition_anchor_terms(nutrition_terms, diet_terms)

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
        anchor_terms = nutrition_anchor_terms if _needs_nutrition_anchor(chunk) else []
        queries.append(
            _join_parts(
                [
                    or_block(condition_terms + clinical_terms, 8),
                    or_block(chunk, 5),
                    or_block(anchor_terms, 4),
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
                    or_block(doc_type_terms, 6),
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
