from __future__ import annotations

from urllib.parse import urlparse

SOURCE_BONUS = {
    "official": 9,
    "pubmed": 6,
    "europepmc": 6,
    "openalex": 5,
    "crossref": 4,
}

POSITIVE_TITLE_RULES = {
    "guideline": 9,
    "guidelines": 9,
    "clinical practice guideline": 10,
    "food-based dietary guideline": 9,
    "consensus": 8,
    "consensus report": 8,
    "statement": 7,
    "scientific statement": 8,
    "position statement": 8,
    "position paper": 8,
    "practice advisory": 7,
    "practice guidance": 8,
    "guidance statement": 8,
    "clinical practice update": 8,
    "guideline update": 8,
    "joint statement": 7,
    "joint guideline": 8,
    "clinical guidance": 7,
    "best practice advice": 7,
    "clinical decision pathway": 8,
    "decision pathway": 7,
    "living guideline": 9,
    "standards of care": 9,
    "consensus guidance": 8,
    "clinical pathway": 7,
    "care pathway": 7,
    "recommendation": 7,
    "clinical practice recommendation": 7,
    "clinical practice recommendations": 7,
    "scientific advisory": 7,
    "systematic review": 8,
    "meta-analysis": 8,
    "meta analysis": 8,
    "network meta-analysis": 8,
    "network meta analysis": 8,
    "umbrella review": 8,
    "overview of reviews": 7,
    "review of reviews": 7,
    "rapid review": 6,
    "living systematic review": 7,
    "scoping review": 6,
    "integrative review": 6,
    "randomized": 7,
    "randomised": 7,
    "trial": 6,
    "controlled trial": 7,
    "feasibility": 4,
    "pilot": 3,
    "framework": 6,
    "questionnaire": 6,
    "instrument": 5,
    "adherence": 4,
    "implementation": 4,
    "implementation science": 5,
    "implementation strategy": 4,
    "implementation strategies": 4,
    "implementation outcomes": 4,
    "implementation framework": 5,
    "implementation frameworks": 5,
    "implementation facilitation": 4,
    "implementation fidelity": 4,
    "implementation determinant": 4,
    "implementation determinants": 4,
    "implementation barrier": 4,
    "implementation barriers": 4,
    "implementation facilitator": 4,
    "implementation facilitators": 4,
    "hybrid effectiveness-implementation": 5,
    "hybrid effectiveness implementation": 5,
    "consolidated framework for implementation research": 5,
    "cfir": 4,
    "re-aim": 4,
    "normalization process theory": 4,
    "theoretical domains framework": 4,
    "practice facilitation": 4,
    "shared decision making": 4,
    "behavior change technique": 4,
    "self-management support": 4,
    "knowledge translation": 4,
    "food is medicine": 5,
    "food as medicine": 5,
    "food is medicine intervention": 5,
    "food as medicine intervention": 5,
    "produce prescription": 5,
    "produce prescriptions": 5,
    "produce prescription program": 5,
    "medically tailored meal": 5,
    "medically tailored meals": 5,
    "medically tailored grocery": 5,
    "medically tailored groceries": 5,
    "teaching kitchen": 5,
    "teaching kitchens": 5,
    "culinary medicine": 5,
    "culinary": 4,
    "food literacy": 5,
    "food and nutrition literacy": 5,
    "food agency": 4,
    "nutrition literacy": 5,
    "health literacy": 4,
    "nutrition education": 4,
    "nutrition counseling": 4,
    "nutrition counselling": 4,
    "dietary counseling": 4,
    "dietary counselling": 4,
    "medical nutrition therapy": 5,
    "registered dietitian": 4,
    "registered dietitian nutritionist": 4,
    "dietitian-led": 4,
    "dietitian led": 4,
    "dietitian-led intervention": 4,
    "dietitian led intervention": 4,
    "health coaching": 3,
    "meal planning": 4,
    "meal preparation": 4,
    "home cooking": 4,
    "cooking skills": 4,
    "cooking confidence": 4,
    "shared meals": 4,
    "nutrition security": 4,
    "mediterranean": 3,
    "mind diet": 4,
    "dash": 3,
    "plant-based": 3,
    "portfolio diet": 4,
    "nordic diet": 4,
    "planetary health diet": 4,
    "eat-lancet": 4,
    "vegetarian": 3,
    "vegan": 3,
    "keto": 3,
    "low-carb": 3,
    "lifestyle intervention": 4,
    "lifestyle modification": 4,
    "therapeutic lifestyle changes": 5,
    "mafld": 4,
    "masld": 4,
    "mash": 4,
    "nash": 4,
    "nonalcoholic fatty liver disease": 4,
    "non-alcoholic fatty liver disease": 4,
    "nonalcoholic steatohepatitis": 4,
    "non-alcoholic steatohepatitis": 4,
    "metabolic dysfunction-associated fatty liver disease": 4,
    "metabolic dysfunction associated fatty liver disease": 4,
    "metabolic dysfunction-associated steatotic liver disease": 4,
    "steatotic liver disease": 4,
}

NEGATIVE_TITLE_RULES = {
    "editorial": -7,
    "commentary": -6,
    "letter": -5,
    "case report": -5,
    "protocol": -2,
    "correction": -10,
    "retraction": -12,
    "pediatric": -6,
    "paediatric": -6,
    "child": -6,
    "children": -6,
    "adolescent": -5,
    "mouse": -8,
    "mice": -8,
    "rat": -8,
    "animal": -8,
    "in vitro": -7,
    "psychiatry": -5,
    "clozapine": -6,
    "stroke center": -6,
}

OUT_OF_SCOPE_DOMAINS = {
    "pediatric_population": {
        "tokens": [
            "pediatric",
            "paediatric",
            "child",
            "children",
            "adolescent",
            "adolescents",
            "youth",
            "schoolchildren",
            "infant",
            "neonate",
            "pregnancy",
            "gestational",
        ],
        "penalty": -8,
    },
    "animal_or_preclinical": {
        "tokens": [
            "mouse",
            "mice",
            "rat",
            "rats",
            "murine",
            "animal model",
            "zebrafish",
            "swine",
            "preclinical",
        ],
        "penalty": -10,
    },
    "bench_or_cellular": {
        "tokens": [
            "in vitro",
            "cell culture",
            "cell line",
            "hepatocyte",
            "adipocyte",
            "gene expression",
            "molecular docking",
            "metabolomics only",
            "proteomics only",
        ],
        "penalty": -8,
    },
    "psychiatric_drug_focus": {
        "tokens": [
            "clozapine",
            "olanzapine",
            "antipsychotic",
            "schizophrenia",
            "bipolar disorder",
            "major depressive disorder",
            "psychiatric inpatient",
        ],
        "penalty": -7,
    },
    "acute_hospital_or_surgery": {
        "tokens": [
            "intensive care",
            "icu",
            "perioperative",
            "postoperative",
            "surgery",
            "surgical",
            "stroke center",
            "acute stroke",
            "enteral nutrition",
            "parenteral nutrition",
        ],
        "penalty": -6,
    },
    "non_human_or_agriculture": {
        "tokens": [
            "livestock",
            "cattle",
            "dairy cow",
            "broiler",
            "aquaculture",
            "crop yield",
            "soil microbiome",
            "animal feed",
        ],
        "penalty": -10,
    },
}

OOS_RESCUE_TOKENS = [
    "adult",
    "adults",
    "clinical practice guideline",
    "guideline",
    "consensus",
    "consensus report",
    "standards of care",
    "clinical pathway",
    "care pathway",
    "systematic review",
    "meta-analysis",
    "randomized controlled trial",
    "lifestyle intervention",
    "lifestyle modification",
    "therapeutic lifestyle changes",
    "medical nutrition therapy",
    "obesity",
    "type 2 diabetes",
    "hypertension",
    "cardiometabolic",
    "food literacy",
    "food and nutrition literacy",
    "implementation",
    "home cooking",
    "meal preparation",
    "food is medicine",
    "food as medicine",
    "medically tailored meal",
    "medically tailored meals",
]

WORKSTREAM_BONUS = {
    "busca1": {
        "food guideline": 6,
        "guia alimentar": 6,
        "dietary guideline": 6,
        "food-based dietary guideline": 7,
        "policy": 3,
        "report": 3,
        "healthy eating": 4,
        "food literacy": 3,
        "food and nutrition literacy": 4,
        "food agency": 3,
        "health literacy": 3,
        "nutrition education": 3,
        "food is medicine": 5,
        "food as medicine": 5,
        "food as medicine intervention": 5,
        "produce prescription": 5,
        "produce prescriptions": 5,
        "medically tailored meal": 5,
        "medically tailored meals": 5,
        "medically tailored grocery": 5,
        "medically tailored groceries": 5,
        "teaching kitchen": 5,
        "teaching kitchens": 5,
        "culinary medicine": 4,
        "commensality": 3,
        "shared meals": 3,
        "culinary": 3,
        "home cooking": 3,
        "meal preparation": 3,
        "cooking skills": 3,
        "obesity": 3,
        "lifestyle": 2,
        "nutrition counseling": 3,
        "nutrition counselling": 3,
        "dietary counseling": 3,
        "dietary counselling": 3,
    },
    "busca2a": {
        "guideline": 5,
        "consensus": 5,
        "consensus report": 5,
        "consensus guidance": 5,
        "statement": 5,
        "practice guidance": 5,
        "guidance statement": 5,
        "clinical practice update": 5,
        "guideline update": 5,
        "best practice advice": 5,
        "joint statement": 5,
        "joint guideline": 5,
        "standards of care": 5,
        "clinical pathway": 5,
        "care pathway": 5,
        "clinical decision pathway": 5,
        "decision pathway": 4,
        "clinical practice recommendation": 5,
        "clinical practice recommendations": 5,
        "scientific advisory": 4,
        "position paper": 5,
        "diabetes": 4,
        "hypertension": 4,
        "dyslipidemia": 4,
        "dyslipidaemia": 4,
        "hyperlipidemia": 4,
        "hyperlipidaemia": 4,
        "hypercholesterolemia": 4,
        "hypercholesterolaemia": 4,
        "cardiovascular": 4,
        "metabolic syndrome": 4,
        "masld": 4,
        "nafld": 4,
        "mafld": 4,
        "mash": 4,
        "nash": 4,
        "nonalcoholic fatty liver disease": 4,
        "non-alcoholic fatty liver disease": 4,
        "nonalcoholic steatohepatitis": 4,
        "non-alcoholic steatohepatitis": 4,
        "metabolic dysfunction-associated fatty liver disease": 4,
        "metabolic dysfunction-associated steatotic liver disease": 4,
        "steatotic liver disease": 4,
        "medical nutrition therapy": 4,
        "registered dietitian": 3,
        "registered dietitian nutritionist": 3,
        "dietitian-led": 3,
        "dietitian led": 3,
        "lifestyle modification": 3,
        "therapeutic lifestyle changes": 3,
        "hba1c": 3,
        "blood pressure": 3,
        "ldl": 3,
    },
    "busca2b": {
        "trial": 5,
        "randomized": 5,
        "adherence": 4,
        "feasibility": 4,
        "implementation": 4,
        "implementation science": 4,
        "implementation strategy": 4,
        "implementation strategies": 4,
        "implementation outcomes": 4,
        "implementation framework": 5,
        "implementation frameworks": 5,
        "implementation facilitation": 4,
        "implementation fidelity": 4,
        "implementation determinant": 4,
        "implementation determinants": 4,
        "implementation barrier": 4,
        "implementation barriers": 4,
        "implementation facilitator": 4,
        "implementation facilitators": 4,
        "hybrid effectiveness-implementation": 5,
        "hybrid effectiveness implementation": 5,
        "consolidated framework for implementation research": 5,
        "cfir": 4,
        "re-aim": 4,
        "normalization process theory": 4,
        "theoretical domains framework": 4,
        "practice facilitation": 4,
        "shared decision making": 4,
        "knowledge translation": 4,
        "mediterranean": 4,
        "mind diet": 4,
        "dash": 4,
        "plant-based": 4,
        "vegetarian": 4,
        "vegan": 4,
        "portfolio diet": 4,
        "nordic diet": 4,
        "eat-lancet": 4,
        "planetary health diet": 4,
        "keto": 4,
        "low-carb": 4,
        "food literacy": 3,
        "food and nutrition literacy": 3,
        "food agency": 3,
        "nutrition literacy": 3,
        "nutrition education": 3,
        "food is medicine": 4,
        "food as medicine": 4,
        "food as medicine intervention": 4,
        "produce prescription": 4,
        "produce prescriptions": 4,
        "produce prescription program": 4,
        "medically tailored meal": 5,
        "medically tailored meals": 5,
        "medically tailored grocery": 4,
        "medically tailored groceries": 4,
        "teaching kitchen": 4,
        "teaching kitchens": 4,
        "culinary medicine": 4,
        "nutrition counseling": 3,
        "nutrition counselling": 3,
        "dietary counseling": 3,
        "dietary counselling": 3,
        "medical nutrition therapy": 4,
        "registered dietitian": 3,
        "registered dietitian nutritionist": 3,
        "dietitian-led": 3,
        "dietitian led": 3,
        "dietitian-led intervention": 4,
        "dietitian led intervention": 4,
        "health coaching": 3,
        "culinary": 3,
        "home cooking": 3,
        "meal preparation": 3,
        "self-monitoring": 3,
        "lifestyle intervention": 4,
        "lifestyle modification": 4,
        "therapeutic lifestyle changes": 4,
        "network meta-analysis": 5,
        "network meta analysis": 5,
        "rapid review": 3,
        "living systematic review": 4,
        "dyslipidemia": 4,
        "dyslipidaemia": 4,
        "hyperlipidemia": 4,
        "hyperlipidaemia": 4,
        "hypercholesterolemia": 4,
        "hypercholesterolaemia": 4,
        "masld": 4,
        "nafld": 4,
        "mash": 4,
        "nash": 4,
        "nonalcoholic fatty liver disease": 4,
        "non-alcoholic fatty liver disease": 4,
        "nonalcoholic steatohepatitis": 4,
        "non-alcoholic steatohepatitis": 4,
        "metabolic dysfunction-associated fatty liver disease": 4,
        "metabolic dysfunction-associated steatotic liver disease": 4,
        "steatotic liver disease": 4,
    },
    "a3": {
        "framework": 6,
        "questionnaire": 6,
        "instrument": 5,
        "food literacy": 5,
        "food and nutrition literacy": 5,
        "food agency": 5,
        "nutrition literacy": 5,
        "health literacy": 4,
        "nutrition education": 4,
        "culinary": 5,
        "cooking skills": 5,
        "cooking confidence": 4,
        "home cooking": 4,
        "meal preparation": 4,
        "commensality": 5,
        "shared meals": 4,
        "behavior": 4,
        "implementation": 4,
        "implementation framework": 5,
        "implementation frameworks": 5,
        "implementation strategy": 4,
        "implementation strategies": 4,
        "implementation outcomes": 4,
        "hybrid effectiveness-implementation": 5,
        "hybrid effectiveness implementation": 5,
        "consolidated framework for implementation research": 5,
        "cfir": 4,
        "re-aim": 4,
        "normalization process theory": 4,
        "theoretical domains framework": 4,
        "knowledge translation": 3,
        "dietary counseling": 3,
        "dietary counselling": 3,
    },
    "artigo3_framework": {
        "framework": 6,
        "questionnaire": 6,
        "instrument": 5,
        "food literacy": 5,
        "food and nutrition literacy": 5,
        "food agency": 5,
        "nutrition literacy": 5,
        "health literacy": 4,
        "nutrition education": 4,
        "culinary": 5,
        "cooking skills": 5,
        "cooking confidence": 4,
        "home cooking": 4,
        "meal preparation": 4,
        "commensality": 5,
        "shared meals": 4,
        "behavior": 4,
        "implementation": 4,
        "implementation framework": 5,
        "implementation frameworks": 5,
        "implementation strategy": 4,
        "implementation strategies": 4,
        "implementation outcomes": 4,
        "hybrid effectiveness-implementation": 5,
        "hybrid effectiveness implementation": 5,
        "consolidated framework for implementation research": 5,
        "cfir": 4,
        "re-aim": 4,
        "normalization process theory": 4,
        "theoretical domains framework": 4,
        "knowledge translation": 3,
        "dietary counseling": 3,
        "dietary counselling": 3,
    },
}

IMPLEMENTATION_DESIGN_BONUS = {
    "busca2b": {
        "hybrid type 1": 4,
        "hybrid type 2": 5,
        "hybrid type 3": 5,
        "implementation trial": 4,
        "implementation evaluation": 4,
        "process evaluation": 3,
        "quality improvement": 3,
        "quality improvement study": 4,
        "real-world evidence": 3,
        "real-world implementation": 4,
        "scale-up": 3,
        "scale up": 3,
        "scale-out": 3,
        "scale out": 3,
        "program implementation": 3,
        "care delivery": 2,
        "service delivery": 2,
    },
    "a3": {
        "hybrid type 1": 3,
        "hybrid type 2": 4,
        "hybrid type 3": 4,
        "implementation trial": 3,
        "implementation evaluation": 3,
        "process evaluation": 3,
        "quality improvement": 2,
        "real-world implementation": 3,
        "scale-up": 2,
        "scale up": 2,
    },
    "artigo3_framework": {
        "hybrid type 1": 3,
        "hybrid type 2": 4,
        "hybrid type 3": 4,
        "implementation trial": 3,
        "implementation evaluation": 3,
        "process evaluation": 3,
        "quality improvement": 2,
        "real-world implementation": 3,
        "scale-up": 2,
        "scale up": 2,
    },
}

WORKSTREAM_SIGNAL_GROUPS = {
    "busca1": {
        "condition": ["obesity", "overweight", "obesidade", "sobrepeso"],
        "document": [
            "guideline",
            "guidelines",
            "report",
            "policy",
            "framework",
            "guia alimentar",
            "dietary guideline",
        ],
        "mev_nutrition": [
            "healthy eating",
            "food literacy",
            "food is medicine",
            "food as medicine",
            "produce prescription",
            "produce prescriptions",
            "medically tailored meal",
            "medically tailored meals",
            "medically tailored grocery",
            "medically tailored groceries",
            "teaching kitchen",
            "teaching kitchens",
            "culinary medicine",
            "culinary",
            "commensality",
            "meal planning",
            "lifestyle medicine",
        ],
    },
    "busca2a": {
        "condition": [
            "obesity",
            "diabetes",
            "hypertension",
            "dyslipidemia",
            "dyslipidaemia",
            "hyperlipidemia",
            "hyperlipidaemia",
            "hypercholesterolemia",
            "hypercholesterolaemia",
            "cardiovascular",
            "metabolic syndrome",
            "masld",
            "nafld",
            "mafld",
        ],
        "document": [
            "guideline",
            "consensus",
            "statement",
            "recommendation",
        ],
        "outcome": [
            "hba1c",
            "blood pressure",
            "ldl",
            "glycemic",
            "lipid",
            "cardiometabolic",
        ],
    },
    "busca2b": {
        "condition": [
            "obesity",
            "diabetes",
            "hypertension",
            "dyslipidemia",
            "dyslipidaemia",
            "hyperlipidemia",
            "hyperlipidaemia",
            "hypercholesterolemia",
            "hypercholesterolaemia",
            "cardiometabolic",
            "masld",
            "nafld",
            "mafld",
            "mash",
            "nash",
            "fatty liver",
            "steatotic liver disease",
            "metabolic dysfunction-associated steatotic liver disease",
            "metabolic dysfunction-associated fatty liver disease",
            "nonalcoholic fatty liver disease",
            "non-alcoholic fatty liver disease",
            "nonalcoholic steatohepatitis",
            "non-alcoholic steatohepatitis",
        ],
        "intervention": [
            "mediterranean",
            "dash",
            "mind diet",
            "plant-based",
            "vegetarian",
            "vegan",
            "portfolio diet",
            "nordic diet",
            "planetary health diet",
            "eat-lancet",
            "keto",
            "low-carb",
            "meal replacement",
            "food is medicine",
            "food as medicine",
            "produce prescription",
            "produce prescriptions",
            "medically tailored meal",
            "medically tailored meals",
            "medically tailored grocery",
            "medically tailored groceries",
        ],
        "implementation": [
            "adherence",
            "implementation",
            "implementation science",
            "implementation fidelity",
            "knowledge translation",
            "feasibility",
            "behavior",
            "food agency",
            "lifestyle intervention",
            "lifestyle modification",
            "therapeutic lifestyle changes",
            "teaching kitchen",
            "teaching kitchens",
            "culinary medicine",
            "counseling",
            "counselling",
        ],
        "design": [
            "trial",
            "randomized",
            "systematic review",
            "meta-analysis",
            "umbrella review",
            "network meta-analysis",
            "rapid review",
            "living systematic review",
        ],
    },
    "a3": {
        "construct": [
            "framework",
            "questionnaire",
            "instrument",
            "scale",
            "validation",
            "psychometric",
        ],
        "domain": [
            "food literacy",
            "food agency",
            "culinary",
            "commensality",
            "meal planning",
            "self-efficacy",
            "behavior change",
        ],
        "mev": ["lifestyle medicine", "nutrition", "implementation"],
    },
    "artigo3_framework": {
        "construct": [
            "framework",
            "questionnaire",
            "instrument",
            "scale",
            "validation",
            "psychometric",
        ],
        "domain": [
            "food literacy",
            "food agency",
            "culinary",
            "commensality",
            "meal planning",
            "self-efficacy",
            "behavior change",
        ],
        "mev": ["lifestyle medicine", "nutrition", "implementation"],
    },
}

DIRECT_DOWNLOAD_HINTS = [
    ".pdf",
    "/pdf",
    "pdfdirect",
    "download",
    "fulltext",
    "full-text",
    "epdf",
    "viewarticle",
    "article/download",
    "article-pdf",
]

OPEN_ACCESS_HINTS = [
    "open access",
    "free full text",
    "pmc",
    "pmcid",
    "pubmed central",
    "creativecommons",
    "creative commons",
    "biomedcentral",
    "frontiersin",
    "mdpi",
    "plos",
    "scielo",
]

DATA_RICH_HINTS = [
    "supplement",
    "supplementary",
    "appendix",
    "questionnaire",
    "scale",
    "instrument",
    "protocol",
    "checklist",
    "dataset",
    "data availability",
]

HIGH_VALUE_DOWNLOAD_TOKENS = [
    "guideline",
    "guidelines",
    "consensus",
    "statement",
    "recommendation",
    "systematic review",
    "meta-analysis",
    "umbrella review",
    "randomized",
    "trial",
    "framework",
    "questionnaire",
    "instrument",
    "validation",
    "psychometric",
]


def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def _download_signal_score(text: str, url: str) -> int:
    signal = 0
    if _contains_any(url, DIRECT_DOWNLOAD_HINTS):
        signal += 3
    if _contains_any(text, OPEN_ACCESS_HINTS):
        signal += 2
    if _contains_any(text, DATA_RICH_HINTS):
        signal += 2
    return signal


def _workstream_signal_hits(text: str, workstream: str) -> dict[str, int]:
    hits = {}
    for group_name, tokens in WORKSTREAM_SIGNAL_GROUPS.get(workstream, {}).items():
        hits[group_name] = sum(1 for token in tokens if token in text)
    return hits


def _workstream_coherence_bonus(text: str, workstream: str) -> int:
    hits = _workstream_signal_hits(text, workstream)
    matched_groups = sum(1 for count in hits.values() if count > 0)
    bonus = 0

    if matched_groups >= 2:
        bonus += 4
    if matched_groups >= 3:
        bonus += 4
    if any(count >= 2 for count in hits.values()):
        bonus += 2

    return bonus


def _out_of_scope_profile(text: str) -> tuple[list[str], int]:
    flags: list[str] = []
    penalty = 0
    for domain, config in OUT_OF_SCOPE_DOMAINS.items():
        tokens = config["tokens"]
        if _contains_any(text, tokens):
            flags.append(domain)
            penalty += config["penalty"]
    return flags, penalty


def _out_of_scope_rescue_bonus(text: str, workstream: str) -> int:
    rescue = 0
    if _contains_any(text, OOS_RESCUE_TOKENS):
        rescue += 3
    if sum(1 for count in _workstream_signal_hits(text, workstream).values() if count) >= 3:
        rescue += 4
    return rescue


def _should_hard_exclude_out_of_scope(text: str, workstream: str) -> bool:
    flags, penalty = _out_of_scope_profile(text)
    if not flags:
        return False
    rescue = _out_of_scope_rescue_bonus(text, workstream)
    if rescue >= 7:
        return False
    return penalty <= -10 or len(flags) >= 2


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.netloc or "").lower()


def _match_weighted_points(text: str, points_map: dict[str, int]) -> int:
    score = 0
    for token, points in points_map.items():
        if token and token.lower() in text:
            score += points
    return score


def _implementation_design_bonus(text: str, workstream: str) -> int:
    return _match_weighted_points(text, IMPLEMENTATION_DESIGN_BONUS.get(workstream, {}))


def _editorial_authority_score(record: dict, scoring_rules: dict) -> int:
    authority_rules = scoring_rules.get("editorial_authority_points", {})
    journal = (record.get("journal") or "").lower()
    source_institution = (record.get("source_institution") or "").lower()
    url = (
        record.get("url")
        or record.get("final_url")
        or record.get("original_url")
        or ""
    ).lower()
    domain = _extract_domain(url)

    score = 0
    score += _match_weighted_points(journal, authority_rules.get("journals", {}))
    score += _match_weighted_points(
        source_institution,
        authority_rules.get("institutions", {}),
    )
    score += _match_weighted_points(domain, authority_rules.get("domains", {}))
    return score


def _editorial_priority_tier(score: int) -> str:
    if score >= 12:
        return "a1_proxy_high"
    if score >= 7:
        return "a1_proxy_moderate"
    if score >= 3:
        return "editorial_priority"
    return "standard"


def score_record(record: dict, scoring_rules: dict, workstream: str) -> dict:
    title = (record.get("title") or "").lower()
    url = (record.get("url") or "").lower()
    doi = (record.get("doi") or "").lower()
    abstract = (record.get("abstract") or record.get("summary") or "").lower()
    journal = (record.get("journal") or "").lower()
    source_institution = (record.get("source_institution") or "").lower()
    text = f"{title} {url} {doi} {abstract} {journal} {source_institution}"

    score = 0

    for kw, points in scoring_rules.get("keyword_points", {}).items():
        if kw.lower() in text:
            score += points

    score += scoring_rules.get("source_points", {}).get(record.get("source"), 0)
    score += scoring_rules.get("workstream_points", {}).get(workstream, 0)
    score += SOURCE_BONUS.get(record.get("source", ""), 0)

    for kw, pts in POSITIVE_TITLE_RULES.items():
        if kw in text:
            score += pts

    for kw, pts in NEGATIVE_TITLE_RULES.items():
        if kw in text:
            score += pts

    for kw, pts in WORKSTREAM_BONUS.get(workstream, {}).items():
        if kw in text:
            score += pts

    score += _implementation_design_bonus(text, workstream)

    out_of_scope_flags, out_of_scope_penalty = _out_of_scope_profile(text)
    editorial_score = _editorial_authority_score(record, scoring_rules)
    score += _download_signal_score(text, url)
    score += _workstream_coherence_bonus(text, workstream)
    score += out_of_scope_penalty
    score += _out_of_scope_rescue_bonus(text, workstream)
    score += editorial_score

    record["out_of_scope_flags"] = out_of_scope_flags
    record["out_of_scope_penalty"] = out_of_scope_penalty
    record["editorial_priority_score"] = editorial_score
    record["editorial_priority_tier"] = _editorial_priority_tier(editorial_score)
    record["relevance_score"] = score
    return record


def keep_candidate_for_download(record: dict, workstream: str) -> bool:
    text = " ".join(
        [
            str(record.get("title") or ""),
            str(record.get("abstract") or ""),
            str(record.get("url") or ""),
        ]
    ).lower()
    if _should_hard_exclude_out_of_scope(text, workstream):
        return False
    score = float(record.get("relevance_score") or 0)
    if score < 7:
        return False
    if any(t in text for t in ("editorial", "commentary", "letter", "case report")):
        return False
    return True
