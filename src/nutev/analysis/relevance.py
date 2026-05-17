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

EVIDENCE_RULES = {
    "clinical practice guideline": 12,
    "guideline": 10,
    "guidelines": 10,
    "scientific statement": 10,
    "consensus": 9,
    "position statement": 8,
    "systematic review": 9,
    "meta-analysis": 9,
    "meta analysis": 9,
    "umbrella review": 9,
    "randomized controlled trial": 8,
    "randomised controlled trial": 8,
    "controlled trial": 7,
    "pragmatic trial": 7,
    "framework": 6,
    "questionnaire": 6,
    "instrument": 6,
    "scale": 5,
}

CLINICAL_TARGET_RULES = {
    "obesity": 4,
    "overweight": 3,
    "cardiometabolic": 5,
    "cardiovascular": 4,
    "metabolic syndrome": 4,
    "diabetes": 4,
    "type 2 diabetes": 5,
    "hypertension": 4,
    "dyslipidemia": 4,
    "masld": 4,
    "nafld": 4,
    "obesidade": 4,
    "risco cardiometabólico": 5,
    "hipertensão": 4,
    "dislipidemia": 4,
    "esteatose hepática": 4,
}

IMPLEMENTATION_RULES = {
    "adherence": 4,
    "acceptability": 4,
    "feasibility": 4,
    "implementation": 4,
    "implementation science": 5,
    "barrier": 3,
    "facilitator": 3,
    "behavior change": 4,
    "self-efficacy": 4,
    "self efficacy": 4,
    "food literacy": 5,
    "culinary medicine": 4,
    "commensality": 4,
    "meal planning": 3,
    "shared meals": 3,
    "adesão": 4,
    "aceitabilidade": 4,
    "viabilidade": 4,
    "implementação": 4,
    "mudança de comportamento": 4,
    "autoeficácia": 4,
    "literacia alimentar": 5,
    "medicina culinária": 4,
    "comensalidade": 4,
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
        "food literacy": 4,
        "commensality": 4,
        "culinary": 4,
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
        "food literacy": 4,
        "culinary": 4,
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


def _normalize_text(value: object) -> str:
    return str(value or "").lower()


def _score_rules(text: str, rules: dict[str, int]) -> int:
    return sum(points for keyword, points in rules.items() if keyword in text)


def score_record(record: dict, scoring_rules: dict, workstream: str) -> dict:
    title_text = _normalize_text(record.get("title"))
    abstract_text = _normalize_text(record.get("abstract"))
    extracted_text = _normalize_text(record.get("extracted_text"))[:12000]
    url_text = _normalize_text(record.get("url"))
    doi_text = _normalize_text(record.get("doi"))
    metadata_text = " ".join(part for part in [title_text, abstract_text, url_text, doi_text] if part)
    rich_text = " ".join(part for part in [title_text, abstract_text, extracted_text] if part)

    score = 0

    for keyword, points in scoring_rules.get("keyword_points", {}).items():
        if keyword.lower() in metadata_text:
            score += points
        elif keyword.lower() in extracted_text:
            score += max(1, points // 2)

    source = _normalize_text(record.get("source"))
    score += scoring_rules.get("source_points", {}).get(source, 0)
    score += scoring_rules.get("workstream_points", {}).get(workstream, 0)
    score += SOURCE_BONUS.get(source, 0)

    if source == "official":
        try:
            score += int(record.get("authority") or 0) * 2
        except (TypeError, ValueError):
            pass

    score += _score_rules(title_text, POSITIVE_TITLE_RULES)
    score += _score_rules(title_text, EVIDENCE_RULES)
    score += _score_rules(metadata_text, CLINICAL_TARGET_RULES)
    score += _score_rules(rich_text, IMPLEMENTATION_RULES)
    score += _score_rules(metadata_text, NEGATIVE_TITLE_RULES)
    score += _score_rules(rich_text, WORKSTREAM_BONUS.get(workstream, {}))

    if extracted_text:
        if _score_rules(extracted_text, EVIDENCE_RULES):
            score += 4
        if _score_rules(extracted_text, CLINICAL_TARGET_RULES):
            score += 3
        if _score_rules(extracted_text, IMPLEMENTATION_RULES):
            score += 3

    if ".pdf" in url_text or "/pdf" in url_text or "pdfdirect" in url_text or "download" in url_text:
        score += 2

    if not title_text.strip():
        score -= 8
    if not (title_text or abstract_text or extracted_text).strip():
        score -= 10

    record["relevance_score"] = score
    return record


def keep_candidate_for_download(record: dict, workstream: str) -> bool:
    score = record.get("relevance_score", 0)
    title = _normalize_text(record.get("title"))
    abstract = _normalize_text(record.get("abstract"))
    extracted = _normalize_text(record.get("extracted_text"))[:6000]
    url = _normalize_text(record.get("url"))
    source = _normalize_text(record.get("source"))
    text = " ".join(part for part in [title, abstract, extracted] if part)

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
    if any(token in text for token in hard_drop):
        return False

    if any(token in url for token in ["mostdownload.php", "/tdm/v1/articles/", "content.aspx?aid=", "book/chapter-pdf"]):
        return False

    if source == "official":
        return True

    thresholds = {
        "busca1": 9,
        "busca2a": 9,
        "busca2b": 8,
        "a3": 6,
        "artigo3_framework": 6,
    }
    return score >= thresholds.get(workstream, 7)
