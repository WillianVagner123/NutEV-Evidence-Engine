"""Rich multilingual thematic detection with evidence snippets.

The A/B/C/D coding gives the high-level scoping frame; this adds the *granular*
layer your grey-literature script had: named dietary patterns, Lifestyle-Medicine
pillars (sleep/stress/activity/social/food-environment), neuro/mental-health,
eating competencies, food processing (NOVA), and implementation factors —
multilingual (EN/PT/ES) and **config-driven** (``config/thematic_taxonomy.json``).

For every sub-theme it detects, it also extracts the **verbatim evidence
snippet** (a context window around the matched term) so a human reviewer sees
*why* it was flagged and can cite it. It also classifies the document type into an
evidence tier and pulls quantitative nutrition values (macro %, fibre, sodium,
micronutrients) by regex. Everything is assistive and enters human review; no
text is fabricated.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_WS = re.compile(r"\s+")

# Quantitative nutrition patterns (best-effort, multilingual units).
_RE_MACRO = re.compile(r"\b(\d{1,3})\s*[-–]\s*(\d{1,3})\s*%")
_RE_FIBER = re.compile(r"\b(\d{1,3})\s*(?:g|gram|grams|gramas)\s*(?:of\s+)?(?:fiber|fibre|fibra)\b", re.I)
_RE_SODIUM = re.compile(r"\b(\d{1,5})\s*(?:mg|g)\s*(?:of\s+)?(?:sodium|s[oó]dio|sodio)\b", re.I)
_RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")


@lru_cache(maxsize=8)
def _load_taxonomy_cached(path_str: str) -> str:
    return Path(path_str).read_text(encoding="utf-8")


def load_taxonomy(config_root: str | Path) -> dict:
    """Load the thematic taxonomy JSON from ``config_root`` (cached by path)."""
    path = Path(config_root) / "thematic_taxonomy.json"
    return json.loads(_load_taxonomy_cached(str(path)))


def _stem(keyword: str) -> str:
    return keyword.lower().replace("*", "")


def _snippets(text: str, low: str, keyword: str, window: int, max_snips: int) -> list[str]:
    """Return up to ``max_snips`` context windows around ``keyword`` in ``text``."""
    kw = _stem(keyword)
    if not kw:
        return []
    out: list[str] = []
    start = 0
    while len(out) < max_snips:
        idx = low.find(kw, start)
        if idx == -1:
            break
        a = max(0, idx - window)
        b = min(len(text), idx + len(kw) + window)
        out.append(_WS.sub(" ", text[a:b]).strip())
        start = idx + len(kw)
    return out


def detect_themes(text: str, taxonomy: dict, *, window: int | None = None, max_snippets: int = 2) -> dict:
    """Detect sub-themes present in ``text`` with their evidence snippets.

    Returns ``{family: {subtheme: {"present": True, "snippets": [...]}}}`` for the
    sub-themes found. Snippets are verbatim context windows (deduplicated).
    """
    window = window or int(taxonomy.get("snippet_window", 240))
    text = text or ""
    low = text.lower()
    has_text = bool(text.strip())
    result: dict = {}
    for family, subs in taxonomy.get("families", {}).items():
        fam: dict = {}
        for sub, words in subs.items():
            snippets: list[str] = []
            present = False
            for word in words:
                if _stem(word) in low:
                    present = True
                    if has_text:
                        snippets.extend(_snippets(text, low, word, window, max_snippets))
                    if len(snippets) >= max_snippets:
                        break
            if present:
                seen: set[str] = set()
                uniq: list[str] = []
                for snip in snippets:
                    key = snip.lower()[:120]
                    if key in seen:
                        continue
                    seen.add(key)
                    uniq.append(snip)
                fam[sub] = {"present": True, "snippets": uniq[:max_snippets]}
        if fam:
            result[family] = fam
    return result


def classify_doc_type(text: str, taxonomy: dict) -> str:
    """Classify the document into an evidence-tier label (guideline, trial, …)."""
    low = (text or "").lower()
    for label, words in taxonomy.get("doc_type_hints", {}).items():
        if any(w in low for w in words):
            return label
    return "other"


def evidence_weight(doc_type: str, taxonomy: dict) -> int:
    return int(taxonomy.get("evidence_weights", {}).get(doc_type, 1))


def extract_nutrition_values(text: str, taxonomy: dict) -> dict:
    """Pull quantitative nutrition values by regex (best-effort, verbatim)."""
    t = text or ""
    macros = ["-".join(m) + "%" for m in _RE_MACRO.findall(t)]
    fiber = [f"{m}g" for m in _RE_FIBER.findall(t)]
    sodium = [f"{m}" for m in _RE_SODIUM.findall(t)]
    low = t.lower()
    micros = [m for m in taxonomy.get("micronutrients", []) if m in low]
    years = sorted(set(_RE_YEAR.findall(t)))
    return {
        "macros_pct": macros[:6],
        "fiber_g": fiber[:4],
        "sodium": sodium[:4],
        "micronutrients": list(dict.fromkeys(micros))[:12],
        "years": years[-3:],
    }


def _record_text(record: dict) -> str:
    text = str(record.get("extracted_text") or "").strip()
    if text:
        return text
    return " ".join(str(record.get(k, "") or "") for k in ("title", "name", "abstract")).strip()


def thematic_fields(record: dict, taxonomy: dict) -> dict:
    """Compute flat + nested thematic fields for a metadata row.

    Flat (CSV-friendly): ``themes_present`` (pipe-joined ``family:subtheme``),
    ``n_themes``, ``diet_patterns``, ``doc_type``, ``evidence_weight`` and the
    nutrition value strings. Nested: ``themes`` (with snippets) for the JSON detail.
    """
    text = _record_text(record)
    themes = detect_themes(text, taxonomy)
    present: list[str] = []
    diet_patterns: list[str] = []
    for family, subs in themes.items():
        for sub in subs:
            present.append(f"{family}:{sub}")
            if family == "diet_patterns":
                diet_patterns.append(sub)
    doc_type = classify_doc_type(text, taxonomy)
    nutri = extract_nutrition_values(text, taxonomy)
    return {
        "themes": themes,
        "themes_present": "|".join(present),
        "n_themes": len(present),
        "diet_patterns": "|".join(diet_patterns),
        "doc_type": doc_type,
        "evidence_weight": evidence_weight(doc_type, taxonomy),
        "nutrition_macros_pct": "|".join(nutri["macros_pct"]),
        "nutrition_fiber_g": "|".join(nutri["fiber_g"]),
        "nutrition_sodium": "|".join(nutri["sodium"]),
        "nutrition_micronutrients": "|".join(nutri["micronutrients"]),
    }


def evidence_rows(record: dict) -> list[dict]:
    """Tidy per-evidence rows for the evidence table: one row per snippet, each
    carrying the theme, the verbatim evidence and the document's reference."""
    themes = record.get("themes") or {}
    reference = record.get("reference", "")
    out: list[dict] = []
    for family, subs in themes.items():
        for sub, info in subs.items():
            snippets = info.get("snippets") or [""]
            for snip in snippets:
                out.append({
                    "name": record.get("name", ""),
                    "country": record.get("country", ""),
                    "family": family,
                    "subtheme": sub,
                    "evidence_snippet": snip,
                    "doc_type": record.get("doc_type", ""),
                    "evidence_weight": record.get("evidence_weight", ""),
                    "reference": reference,
                    "source_url": record.get("reference_url", ""),
                })
    return out
