from __future__ import annotations

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
    "consensus": 8,
    "statement": 7,
    "scientific statement": 8,
    "position statement": 8,
    "recommendation": 7,
    "systematic review": 8,
    "meta-analysis": 8,
    "meta analysis": 8,
    "umbrella review": 8,
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
    "culinary": 4,
    "food literacy": 5,
    "mediterranean": 3,
    "dash": 3,
    "plant-based": 3,
    "vegetarian": 3,
    "vegan": 3,
    "keto": 3,
    "low-carb": 3,
    "mafld": 5,
    "masld": 5,
    "non-alcoholic fatty liver disease": 5,
    "nonalcoholic fatty liver disease": 5,
    "metabolic dysfunction-associated fatty liver disease": 5,
    "metabolic dysfunction associated fatty liver disease": 5,
    "metabolic dysfunction-associated steatotic liver disease": 5,
    "metabolic dysfunction associated steatotic liver disease": 5,
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

WORKSTREAM_BONUS = {
    "busca1": {
        "food guideline": 6,
        "guia alimentar": 6,
        "dietary guideline": 6,
        "food-based dietary guideline": 6,
        "policy": 3,
        "report": 3,
        "healthy eating": 4,
        "food literacy": 3,
        "commensality": 3,
        "culinary": 3,
        "obesity": 3,
        "lifestyle": 2,
    },
    "busca2a": {
        "guideline": 5,
        "consensus": 5,
        "statement": 5,
        "diabetes": 4,
        "hypertension": 4,
        "dyslipidemia": 4,
        "cardiovascular": 4,
        "metabolic syndrome": 4,
        "masld": 4,
        "mafld": 4,
        "nafld": 4,
        "non-alcoholic fatty liver disease": 4,
        "nonalcoholic fatty liver disease": 4,
        "metabolic dysfunction-associated fatty liver disease": 4,
        "metabolic dysfunction associated fatty liver disease": 4,
        "metabolic dysfunction-associated steatotic liver disease": 4,
        "metabolic dysfunction associated steatotic liver disease": 4,
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
        "mediterranean": 4,
        "dash": 4,
        "plant-based": 4,
        "vegetarian": 4,
        "vegan": 4,
        "keto": 4,
        "low-carb": 4,
        "food literacy": 3,
        "culinary": 3,
        "masld": 3,
        "mafld": 3,
        "non-alcoholic fatty liver disease": 3,
        "nonalcoholic fatty liver disease": 3,
        "metabolic dysfunction-associated steatotic liver disease": 3,
        "metabolic dysfunction associated steatotic liver disease": 3,
    },
    "a3": {
        "framework": 6,
        "questionnaire": 6,
        "instrument": 5,
        "food literacy": 5,
        "culinary": 5,
        "commensality": 5,
        "behavior": 4,
        "implementation": 4,
    },
    "artigo3_framework": {
        "framework": 6,
        "questionnaire": 6,
        "instrument": 5,
        "food literacy": 5,
        "culinary": 5,
        "commensality": 5,
        "behavior": 4,
        "implementation": 4,
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
            "cardiovascular",
            "metabolic syndrome",
            "masld",
            "mafld",
            "nafld",
            "non-alcoholic fatty liver disease",
            "nonalcoholic fatty liver disease",
            "metabolic dysfunction-associated fatty liver disease",
            "metabolic dysfunction associated fatty liver disease",
            "metabolic dysfunction-associated steatotic liver disease",
            "metabolic dysfunction associated steatotic liver disease",
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
            "cardiometabolic",
            "masld",
            "mafld",
            "nafld",
            "non-alcoholic fatty liver disease",
            "nonalcoholic fatty liver disease",
            "metabolic dysfunction-associated steatotic liver disease",
            "metabolic dysfunction associated steatotic liver disease",
        ],
        "intervention": [
            "mediterranean",
            "dash",
            "plant-based",
            "vegetarian",
            "vegan",
            "keto",
            "low-carb",
            "meal replacement",
        ],
        "implementation": [
            "adherence",
            "implementation",
            "feasibility",
            "behavior",
            "lifestyle intervention",
            "counseling",
            "counselling",
        ],
        "design": [
            "trial",
            "randomized",
            "systematic review",
            "meta-analysis",
            "umbrella review",
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


def score_record(record: dict, scoring_rules: dict, workstream: str) -> dict:
    title = (record.get("title") or "").lower()
    url = (record.get("url") or "").lower()
    doi = (record.get("doi") or "").lower()
    abstract = (record.get("abstract") or record.get("summary") or "").lower()
    text = f"{title} {url} {doi} {abstract}"

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

    score += _download_signal_score(text, url)
    score += _workstream_coherence_bonus(text, workstream)

    record["relevance_score"] = score
    return record


def keep_candidate_for_download(record: dict, workstream: str) -> bool:
    score = record.get("relevance_score", 0)
    title = (record.get("title") or "").lower()
    url = (record.get("url") or "").lower()
    source = (record.get("source") or "").lower()
    abstract = (record.get("abstract") or record.get("summary") or "").lower()
    text = f"{title} {url} {abstract}"
    signal_hits = _workstream_signal_hits(text, workstream)
    matched_groups = sum(1 for count in signal_hits.values() if count > 0)

    hard_drop = [
        "editorial",
        "commentary",
        "letter",
        "case report",
        "retraction",
        "pediatric",
        "paediatric",
        "child",
        "children",
        "adolescent",
        "mouse",
        "mice",
        "rat",
        "animal",
        "in vitro",
        "clozapine",
    ]
    if _contains_any(title, hard_drop):
        return False

    blocked_url_tokens = [
        "mostdownload.php",
        "/tdm/v1/articles/",
        "content.aspx?aid=",
        "book/chapter-pdf",
    ]
    if _contains_any(url, blocked_url_tokens):
        return False

    if source == "official":
        return True

    thresholds = {
        "busca1": 7,
        "busca2a": 7,
        "busca2b": 7,
        "a3": 5,
        "artigo3_framework": 5,
    }
    threshold = thresholds.get(workstream, 6)

    has_direct_download_hint = _contains_any(url, DIRECT_DOWNLOAD_HINTS)
    has_high_value_signal = _contains_any(title, HIGH_VALUE_DOWNLOAD_TOKENS)
    has_open_access_signal = _contains_any(text, OPEN_ACCESS_HINTS)
    has_data_rich_signal = _contains_any(text, DATA_RICH_HINTS)

    if matched_groups >= 3 and score >= max(threshold - 2, 4):
        return True

    if has_high_value_signal and has_direct_download_hint and score >= max(threshold - 3, 4):
        return True

    if has_high_value_signal and has_open_access_signal and score >= max(threshold - 2, 4):
        return True

    if has_data_rich_signal and has_direct_download_hint and score >= max(threshold - 2, 4):
        return True

    if workstream in {"a3", "artigo3_framework"} and _contains_any(
        title,
        ["questionnaire", "instrument", "framework", "validation", "psychometric", "scale"],
    ):
        return score >= max(threshold - 2, 4)

    if source in {"pubmed", "europepmc"} and has_high_value_signal:
        return score >= max(threshold - 1, 5)

    return score >= threshold
