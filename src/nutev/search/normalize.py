from __future__ import annotations
import re

DIET_PATTERNS = ["mediterranean","dash","keto","ketogenic","vegetarian","vegan","plant-based","low-carb"]
CLINICAL = ["diabetes","hypertension","dyslipidemia","cardiovascular","metabolic syndrome","nafld","masld"]

def normalize_source(src: str) -> str:
    s=(src or '').lower()
    mapping={"europepmc":"europe_pmc","openalex":"open_alex"}
    return mapping.get(s,s or 'unknown')

def infer_year(text: str) -> str:
    m=re.findall(r"(19\d{2}|20\d{2})", text or "")
    return m[-1] if m else ""

def infer_doc_type(url: str, title: str) -> str:
    u=(url or '').lower(); t=(title or '').lower()
    for ext in ["pdf","docx","doc","xlsx","xls","csv","html","txt"]:
        if f'.{ext}' in u: return ext
    if any(k in t for k in ["guideline","consensus","statement"]): return "guideline"
    if any(k in t for k in ["trial","cohort","review","meta"]): return "study"
    return "unknown"

def infer_diet_pattern(text: str) -> list[str]:
    x=(text or '').lower(); return [d for d in DIET_PATTERNS if d in x]

def infer_clinical_condition(text: str) -> list[str]:
    x=(text or '').lower(); return [c for c in CLINICAL if c in x]
