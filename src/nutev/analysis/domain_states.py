"""Protocol domain states + intensity (0–3) for A/B/C/D, with traceable evidence.

Implements the Article-1 canonical protocol's semantic-role model (§7.2/§7.3):
instead of a bare present/absent boolean, each domain gets a *state* and a
suggested *intensity*, always with the source snippet and page that justify it.

States the machine may suggest (a human may add NOT_REPORTED / NOT_APPLICABLE /
intensity 0 — the machine never asserts absence, since "no keyword" ≠ "concept
absent"):

    NOT_ASSESSED   — no domain keyword found (machine cannot claim absence)  → intensity ""
    MENTIONED      — keyword present, no actionable/operational cue          → intensity 1
    RECOMMENDED    — keyword + an actionable cue (recommend/should/deve)     → intensity 2
    OPERATIONALIZED— keyword + an implementation cue (tool/strategy/target)  → intensity 3

Every suggestion carries ``coding_source="machine_suggestion"`` and
``needs_human_review=True``. This is assistive; two human reviewers decide
(docs/SCIENTIFIC_GOVERNANCE.md, docs/ARTICLE1_DOMAIN_CODING.md). Nothing here
changes the existing ``domain_A..D`` booleans — it adds the richer coding beside
them.
"""
from __future__ import annotations

from nutev.analysis.article1_coding import _ACTIONABLE_CUES, _DOMAIN_KEYWORDS
from nutev.analysis.keyphrases import split_sentences

DOMAINS = ("A", "B", "C", "D")

# Machine-suggestable states, weakest → strongest.
STATE_NOT_ASSESSED = "NOT_ASSESSED"
STATE_MENTIONED = "MENTIONED"
STATE_RECOMMENDED = "RECOMMENDED"
STATE_OPERATIONALIZED = "OPERATIONALIZED"

_LEVEL_TO_STATE = {0: STATE_NOT_ASSESSED, 1: STATE_MENTIONED, 2: STATE_RECOMMENDED, 3: STATE_OPERATIONALIZED}

# Cues that a domain is not merely recommended but *operationalized* — there is a
# concrete instrument, target, strategy, material or monitoring mechanism (EN/PT/ES).
_OPERATIONAL_CUES = (
    "tool", "toolkit", "protocol", "strategy", "strategies", "indicator", "target",
    "goal", "template", "checklist", "step-by-step", "monitoring", "monitor",
    "implementation", "curriculum", "worksheet", "material", "instrument",
    "ferramenta", "protocolo", "estratégia", "indicador", "meta", "modelo",
    "passo a passo", "monitoramento", "implementação", "instrumento", "cartilha",
    "herramienta", "protocolo", "estrategia", "indicador", "material",
)


def _record_text(record: dict) -> str:
    text = str(record.get("extracted_text") or "").strip()
    if text:
        return text
    return " ".join(str(record.get(k, "") or "") for k in ("title", "name", "abstract")).strip()


def _sentence_level(sentence_low: str) -> int:
    """Cue strength of a sentence: 3 operational, 2 actionable, 1 plain mention."""
    if any(cue in sentence_low for cue in _OPERATIONAL_CUES):
        return 3
    if any(cue in sentence_low for cue in _ACTIONABLE_CUES):
        return 2
    return 1


def code_domain_states(record: dict, *, pages: list[str] | None = None) -> dict:
    """Return per-domain state/intensity/evidence for a record.

    ``pages`` (optional) gives per-page text so the evidence carries a page
    number; otherwise page is "". Adds flat fields ``domain_<X>_state``,
    ``domain_<X>_intensity``, ``domain_<X>_evidence``, ``domain_<X>_page`` for
    X in A..D, plus ``domain_coding_source`` and ``domain_states_need_review``.
    """
    if pages:
        sentences: list[tuple[int, str]] = []
        for page_no, page_text in enumerate(pages, start=1):
            for sent in split_sentences(page_text or ""):
                sentences.append((page_no, sent))
    else:
        sentences = [(0, s) for s in split_sentences(_record_text(record))]

    out: dict = {"domain_coding_source": "machine_suggestion", "domain_states_need_review": True}
    for domain in DOMAINS:
        keywords = _DOMAIN_KEYWORDS[domain]
        best_level = 0
        best_page = 0
        best_sentence = ""
        for page_no, sentence in sentences:
            low = sentence.lower()
            if any(kw in low for kw in keywords):
                level = _sentence_level(low)
                if level > best_level:
                    best_level, best_page, best_sentence = level, page_no, sentence.strip()
                    if best_level == 3:
                        break
        out[f"domain_{domain}_state"] = _LEVEL_TO_STATE[best_level]
        # Intensity is a suggestion; NOT_ASSESSED has no intensity (never 0 —
        # only a human may assert "assessed and absent" = 0).
        out[f"domain_{domain}_intensity"] = best_level if best_level > 0 else ""
        out[f"domain_{domain}_evidence"] = best_sentence
        out[f"domain_{domain}_page"] = best_page if best_page > 0 else ""
    return out


def domain_state_rows(record: dict) -> list[dict]:
    """Tidy one-row-per-domain view (for a reviewable states table)."""
    rows: list[dict] = []
    for domain in DOMAINS:
        state = record.get(f"domain_{domain}_state", STATE_NOT_ASSESSED)
        rows.append({
            "name": record.get("name", ""),
            "country": record.get("country", ""),
            "domain": domain,
            "state": state,
            "intensity": record.get(f"domain_{domain}_intensity", ""),
            "evidence": record.get(f"domain_{domain}_evidence", ""),
            "page": record.get(f"domain_{domain}_page", ""),
            "reference": record.get("reference", ""),
            "coding_source": "machine_suggestion",
            "needs_human_review": True,
        })
    return rows
