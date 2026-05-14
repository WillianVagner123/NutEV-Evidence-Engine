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
        "nafld": 4,
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


def score_record(record: dict, scoring_rules: dict, workstream: str) -> dict:
    title = (record.get("title") or "").lower()
    url = (record.get("url") or "").lower()
    doi = (record.get("doi") or "").lower()
    text = f"{title} {url} {doi}"

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

    if ".pdf" in url or "/pdf" in url or "pdfdirect" in url or "download" in url:
        score += 2

    record["relevance_score"] = score
    return record


def keep_candidate_for_download(record: dict, workstream: str) -> bool:
    score = record.get("relevance_score", 0)
    title = (record.get("title") or "").lower()
    url = (record.get("url") or "").lower()
    source = (record.get("source") or "").lower()

    hard_drop = [
        "editorial", "commentary", "letter", "case report", "retraction",
        "pediatric", "paediatric", "child", "children", "adolescent",
        "mouse", "mice", "rat", "animal", "in vitro", "clozapine",
    ]
    if any(tok in title for tok in hard_drop):
        return False

    if any(tok in url for tok in ["mostdownload.php", "/tdm/v1/articles/", "content.aspx?aid=", "book/chapter-pdf"]):
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
    return score >= thresholds.get(workstream, 6)