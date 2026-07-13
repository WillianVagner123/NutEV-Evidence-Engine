from __future__ import annotations

import re

# Canonical dietary-pattern label -> recognition regexes (matched on lowercased
# text). Uses word boundaries so e.g. "dash" no longer matches "dashboard", and
# adds common synonyms/spellings the previous substring list missed.
_DIET_PATTERN_RULES: dict[str, list[str]] = {
    "mediterranean": [r"mediterranean", r"\bmed[- ]?diet\b", r"\bmeddiet\b"],
    "dash": [r"\bdash\b", r"dietary approaches to stop hypertension"],
    "plant-based": [r"plant[-\s]?based", r"plant[-\s]?forward", r"\bflexitarian\b", r"\bpescatarian\b", r"\bplant-rich\b"],
    "vegetarian": [r"\bvegetarian\b", r"\blacto[-\s]?ovo\b"],
    "vegan": [r"\bvegan\b"],
    "low-carb": [r"low[-\s]?carb", r"low[-\s]?carbohydrate", r"carbohydrate[-\s]?restricted"],
    "ketogenic": [r"\bketo\b", r"ketogenic", r"very[-\s]?low[-\s]?carbohydrate", r"\bvlckd\b"],
    "nordic": [r"nordic diet", r"new nordic", r"baltic sea diet"],
    "mind": [r"\bmind diet\b"],
    "portfolio": [r"portfolio diet"],
    "intermittent-fasting": [r"intermittent fasting", r"time[-\s]?restricted", r"alternate[-\s]?day fasting"],
    "paleolithic": [r"\bpaleo\b", r"paleolithic"],
    "atlantic": [r"atlantic diet"],
    "whole-food": [r"whole[-\s]?food plant", r"\bwhole[-\s]?grain\b"],
}
_DIET_PATTERN_COMPILED = {
    label: [re.compile(pat) for pat in pats] for label, pats in _DIET_PATTERN_RULES.items()
}
# Kept for backward-compatible imports.
DIET_PATTERNS = list(_DIET_PATTERN_RULES.keys())
CLINICAL = [
    "diabetes",
    "hypertension",
    "dyslipidemia",
    "cardiovascular",
    "metabolic syndrome",
    "nafld",
    "masld",
]


def normalize_source(src: str) -> str:
    source = (src or "").lower()
    mapping = {"europepmc": "europe_pmc", "openalex": "open_alex"}
    return mapping.get(source, source or "unknown")


def infer_year(text: str) -> str:
    matches = re.findall(r"(19\d{2}|20\d{2})", text or "")
    if matches:
        return matches[-1]
    return ""


def infer_doc_type(url: str, title: str) -> str:
    normalized_url = (url or "").lower()
    normalized_title = (title or "").lower()
    for ext in ["pdf", "docx", "doc", "xlsx", "xls", "csv", "html", "txt"]:
        if f".{ext}" in normalized_url:
            return ext
    if any(
        keyword in normalized_title
        for keyword in ["guideline", "consensus", "statement"]
    ):
        return "guideline"
    if any(
        keyword in normalized_title
        for keyword in ["trial", "cohort", "review", "meta"]
    ):
        return "study"
    return "unknown"


def infer_diet_pattern(text: str) -> list[str]:
    normalized_text = (text or "").lower()
    return [
        label
        for label, regexes in _DIET_PATTERN_COMPILED.items()
        if any(rx.search(normalized_text) for rx in regexes)
    ]


def infer_clinical_condition(text: str) -> list[str]:
    normalized_text = (text or "").lower()
    return [condition for condition in CLINICAL if condition in normalized_text]
