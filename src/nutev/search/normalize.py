from __future__ import annotations

import re

DIET_PATTERNS = [
    "mediterranean",
    "dash",
    "keto",
    "ketogenic",
    "vegetarian",
    "vegan",
    "plant-based",
    "low-carb",
]
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
    return [diet for diet in DIET_PATTERNS if diet in normalized_text]


def infer_clinical_condition(text: str) -> list[str]:
    normalized_text = (text or "").lower()
    return [condition for condition in CLINICAL if condition in normalized_text]
