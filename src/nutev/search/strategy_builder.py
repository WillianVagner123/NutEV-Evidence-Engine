"""Transparent search-strategy builder: question / PICOS → per-base expressions.

Turns a structured research question (concept blocks, optionally tagged with
PICOS roles and MeSH terms) into the exact query string sent to each base, at
three escalating breadth levels:

- ``broad``     — AND of the *core* blocks only (population ∧ intervention): recall.
- ``balanced``  — AND of every conceptual block (adds comparison/outcome/context).
- ``specific``  — balanced + filters (date window, language, publication type): precision.

Within a block, synonyms are OR-ed; across blocks they are AND-ed — the classic
block-building method. Each provider gets syntax it actually understands
(PubMed field tags + MeSH, Europe PMC boolean + PUB_YEAR, Crossref/OpenAlex
free-text + filter params), so the interface can show *exactly* what was sent.

This is additive: it does not replace the taxonomy-driven querypacks the pipeline
already runs — it gives a question-first, auditable way to author a strategy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PROVIDERS = ("pubmed", "europepmc", "crossref", "openalex")
BREADTHS = ("broad", "balanced", "specific")

# PICOS/PECO roles considered "core" for the broad (highest-recall) level.
CORE_ROLES = ("population", "intervention", "exposure")


@dataclass
class Concept:
    """One concept block: a set of synonyms (OR-ed), plus optional MeSH terms.

    ``role`` tags the block for PICOS/PECO breadth logic (population, intervention,
    exposure, comparison, outcome, context). ``mesh`` is used only by PubMed.
    """
    name: str
    terms: list[str]
    role: str = "context"
    mesh: list[str] = field(default_factory=list)


@dataclass
class StrategySpec:
    concepts: list[Concept]
    year_from: int | None = None
    year_to: int | None = None
    languages: list[str] = field(default_factory=list)      # ISO-ish: eng/por/spa
    publication_types: list[str] = field(default_factory=list)  # e.g. Guideline


# --------------------------------------------------------------------------- #
# Parsing helpers — build a StrategySpec from plain dict/JSON input.
# --------------------------------------------------------------------------- #

_PICOS_ROLE_KEYS = {
    "population": "population",
    "patient": "population",
    "intervention": "intervention",
    "exposure": "exposure",
    "comparison": "comparison",
    "comparator": "comparison",
    "outcome": "outcome",
    "context": "context",
    "setting": "context",
}


def _as_terms(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()]


def parse_picos(spec: dict) -> StrategySpec:
    """Build a StrategySpec from a PICOS/PECO dict.

    Each of population/intervention(or exposure)/comparison/outcome/context may be
    a term, a list of synonyms, or a dict ``{"terms": [...], "mesh": [...]}``.
    Optional: ``year_from``, ``year_to``, ``languages``, ``publication_types``.
    """
    concepts: list[Concept] = []
    for key, role in _PICOS_ROLE_KEYS.items():
        if key not in spec:
            continue
        raw = spec[key]
        mesh: list[str] = []
        if isinstance(raw, dict):
            terms = _as_terms(raw.get("terms"))
            mesh = _as_terms(raw.get("mesh"))
        else:
            terms = _as_terms(raw)
        if terms:
            concepts.append(Concept(name=key, terms=terms, role=role, mesh=mesh))
    return StrategySpec(
        concepts=concepts,
        year_from=spec.get("year_from"),
        year_to=spec.get("year_to"),
        languages=_as_terms(spec.get("languages")),
        publication_types=_as_terms(spec.get("publication_types")),
    )


def _split_terms(text: object) -> list[str]:
    """Split a free-text field into synonyms on newlines and semicolons.

    Commas are intentionally *not* delimiters so multiword terms that contain a
    comma survive intact. Blank fragments are dropped.
    """
    if text is None:
        return []
    out: list[str] = []
    for chunk in str(text).replace(";", "\n").split("\n"):
        term = chunk.strip()
        if term:
            out.append(term)
    return out


def picos_from_text(
    population: object = "",
    intervention: object = "",
    exposure: object = "",
    comparison: object = "",
    outcome: object = "",
    context: object = "",
    *,
    year_from: object = None,
    year_to: object = None,
    languages: object = "",
    publication_types: object = "",
) -> dict:
    """Assemble a PICOS dict (the input to :func:`parse_picos`) from raw text
    fields, one synonym per line. Streamlit-free so the UI stays thin and this
    assembly logic is testable on its own. Roles with no terms are omitted, and
    ``year_from``/``year_to`` of 0 or blank are treated as unset.
    """
    def _year(value: object) -> int | None:
        try:
            year = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return year or None

    spec: dict = {}
    for key, value in (
        ("population", population),
        ("intervention", intervention),
        ("exposure", exposure),
        ("comparison", comparison),
        ("outcome", outcome),
        ("context", context),
    ):
        terms = _split_terms(value)
        if terms:
            spec[key] = terms
    year_lo = _year(year_from)
    year_hi = _year(year_to)
    if year_lo is not None:
        spec["year_from"] = year_lo
    if year_hi is not None:
        spec["year_to"] = year_hi
    langs = _split_terms(str(languages).replace(",", "\n"))
    if langs:
        spec["languages"] = langs
    pts = _split_terms(publication_types)
    if pts:
        spec["publication_types"] = pts
    return spec


def parse_concepts(blocks: list) -> StrategySpec:
    """Build a StrategySpec from a plain list of concept blocks.

    Each block is a list of synonyms, or a dict ``{"name","terms","role","mesh"}``.
    Blocks with no explicit role are treated as core ``intervention`` blocks so a
    bare list of concepts still yields a meaningful AND-of-blocks query.
    """
    concepts: list[Concept] = []
    for i, block in enumerate(blocks):
        if isinstance(block, dict):
            terms = _as_terms(block.get("terms"))
            if terms:
                concepts.append(Concept(
                    name=str(block.get("name") or f"block{i + 1}"),
                    terms=terms,
                    role=str(block.get("role") or "intervention"),
                    mesh=_as_terms(block.get("mesh")),
                ))
        else:
            terms = _as_terms(block)
            if terms:
                concepts.append(Concept(name=f"block{i + 1}", terms=terms, role="intervention"))
    return StrategySpec(concepts=concepts)


# --------------------------------------------------------------------------- #
# Breadth selection.
# --------------------------------------------------------------------------- #

def _blocks_for_breadth(spec: StrategySpec, breadth: str) -> list[Concept]:
    if breadth == "broad":
        core = [c for c in spec.concepts if c.role in CORE_ROLES]
        return core or spec.concepts[:1]  # never empty if any concept exists
    return list(spec.concepts)  # balanced + specific use every block


# --------------------------------------------------------------------------- #
# Per-provider term formatting.
# --------------------------------------------------------------------------- #

def _quote(term: str, provider: str) -> str:
    """Phrase-quote multiword terms per provider (single words unquoted)."""
    term = term.strip()
    if " " not in term:
        return term
    return f'"{term}"'


def _pubmed_block(concept: Concept) -> str:
    parts = [f'{_quote(t, "pubmed")}[tiab]' for t in concept.terms]
    parts += [f"{m}[Mesh]" for m in concept.mesh]
    return "(" + " OR ".join(parts) + ")"


def _plain_block(concept: Concept, provider: str) -> str:
    parts = [_quote(t, provider) for t in concept.terms]
    return "(" + " OR ".join(parts) + ")"


def _pubmed_filters(spec: StrategySpec, breadth: str) -> list[str]:
    if breadth != "specific":
        return []
    out: list[str] = []
    if spec.year_from or spec.year_to:
        lo = spec.year_from or 1900
        hi = spec.year_to or 3000
        out.append(f'("{lo}"[dp] : "{hi}"[dp])')
    _lang = {"eng": "english", "por": "portuguese", "spa": "spanish"}
    langs = [f"{_lang.get(x, x)}[lang]" for x in spec.languages]
    if langs:
        out.append("(" + " OR ".join(langs) + ")")
    pts = [f'{_quote(pt, "pubmed")}[pt]' for pt in spec.publication_types]
    if pts:
        out.append("(" + " OR ".join(pts) + ")")
    return out


def _europepmc_filters(spec: StrategySpec, breadth: str) -> list[str]:
    if breadth != "specific":
        return []
    out: list[str] = []
    if spec.year_from or spec.year_to:
        lo = spec.year_from or 1900
        hi = spec.year_to or 3000
        out.append(f"(PUB_YEAR:[{lo} TO {hi}])")
    if spec.languages:
        out.append("(" + " OR ".join(f"LANG:{x}" for x in spec.languages) + ")")
    return out


def _crossref_filter_param(spec: StrategySpec, breadth: str) -> str:
    if breadth != "specific":
        return ""
    parts: list[str] = []
    if spec.year_from:
        parts.append(f"from-pub-date:{spec.year_from}-01-01")
    if spec.year_to:
        parts.append(f"until-pub-date:{spec.year_to}-12-31")
    return ",".join(parts)


def _openalex_filter_param(spec: StrategySpec, breadth: str) -> str:
    if breadth != "specific":
        return ""
    parts: list[str] = []
    if spec.year_from:
        parts.append(f"from_publication_date:{spec.year_from}-01-01")
    if spec.year_to:
        parts.append(f"to_publication_date:{spec.year_to}-12-31")
    if spec.languages:
        parts.append("language:" + "|".join(spec.languages))
    return ",".join(parts)


# --------------------------------------------------------------------------- #
# Public API.
# --------------------------------------------------------------------------- #

def build_query(spec: StrategySpec, provider: str, breadth: str = "balanced") -> str:
    """The exact expression to send to ``provider`` at the given breadth level."""
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider: {provider!r}")
    if breadth not in BREADTHS:
        raise ValueError(f"unknown breadth: {breadth!r}")
    blocks = _blocks_for_breadth(spec, breadth)
    if not blocks:
        return ""

    if provider == "pubmed":
        expr = " AND ".join(_pubmed_block(c) for c in blocks)
        for f in _pubmed_filters(spec, breadth):
            expr += f" AND {f}"
        return expr

    if provider == "europepmc":
        expr = " AND ".join(_plain_block(c, provider) for c in blocks)
        for f in _europepmc_filters(spec, breadth):
            expr += f" AND {f}"
        return expr

    # Crossref / OpenAlex: free-text relevance query + a separate filter param
    # (these APIs do not honour rich boolean in the query itself). Shown as
    # `query=... | filter=...` so the researcher sees exactly what is sent.
    terms = " ".join(_quote(t, provider) for c in blocks for t in c.terms)
    filt = _crossref_filter_param(spec, breadth) if provider == "crossref" else _openalex_filter_param(spec, breadth)
    return f"query={terms} | filter={filt}" if filt else f"query={terms}"


def build_all(spec: StrategySpec) -> dict[str, dict[str, str]]:
    """Every provider × every breadth level: ``{provider: {breadth: expression}}``."""
    return {
        provider: {breadth: build_query(spec, provider, breadth) for breadth in BREADTHS}
        for provider in PROVIDERS
    }
