"""Evidence Gems Bank (§14): rank high-value descriptive findings for Article 1.

A "gem" is a passage or resource of high *descriptive* value for the scoping
review — NOT proof of efficacy and NOT a risk-of-bias / quality score. The score
(0–18) only ranks how useful a document is to *describe* the A/B/C/D landscape,
and every gem stays tied to its source snippet, page and reference.

Scoring dimensions (protocol §14):

    authority verified ............ 0–3   (AACODS endorsement tier)
    currency / in-force ........... 0–2   (publication year)
    A/B/C/D integration breadth ... 0–4   (# domains recommended/operationalized)
    operational specificity ....... 0–3   (# domains OPERATIONALIZED)
    snippet traceability .......... 0–2   (evidence snippet + page present)
    geographic/conceptual novelty . 0–2   (rare domain C / non-anglophone origin)
    implementation material ....... 0–2   (implementation theme / operational tool)
                                     ----
    total ......................... 0–18

Assistive and descriptive only — a human curator approves gems and writes the
paraphrase; nothing here is a claim of quality or effectiveness (§14 warning).
"""
from __future__ import annotations

import json

from nutev.analysis.domain_states import DOMAINS, STATE_OPERATIONALIZED, STATE_RECOMMENDED

_COMMON_ANGLO = {"usa", "united states", "uk", "united kingdom", "england", "canada", "australia", "ireland", "new zealand"}


def _authority_points(record: dict) -> int:
    tier = str(record.get("authority") or "").lower()
    return {"tier_1": 3, "tier_2": 2, "tier_3": 1}.get(tier, 0)


def _currency_points(record: dict) -> int:
    year = str(record.get("reference_version") or record.get("document_version") or record.get("year") or "")
    digits = "".join(c for c in year if c.isdigit())[:4]
    try:
        y = int(digits)
    except ValueError:
        return 0
    if y >= 2022:
        return 2
    if y >= 2018:
        return 1
    return 0


def _positive_domains(record: dict) -> list[str]:
    return [d for d in DOMAINS if record.get(f"domain_{d}_state") in {STATE_RECOMMENDED, STATE_OPERATIONALIZED}]


def _operationalized_domains(record: dict) -> list[str]:
    return [d for d in DOMAINS if record.get(f"domain_{d}_state") == STATE_OPERATIONALIZED]


def _best_evidence(record: dict) -> tuple[str, object]:
    """Return the strongest domain evidence snippet and its page."""
    best_intensity = -1
    snippet, page = "", ""
    for d in DOMAINS:
        inten = record.get(f"domain_{d}_intensity")
        inten = inten if isinstance(inten, int) else -1
        ev = str(record.get(f"domain_{d}_evidence") or "")
        if ev and inten > best_intensity:
            best_intensity, snippet, page = inten, ev, record.get(f"domain_{d}_page", "")
    return snippet, page


def score_gem(record: dict) -> dict:
    """Return the gem score (0–18) with a per-dimension breakdown for a record."""
    positive = _positive_domains(record)
    operationalized = _operationalized_domains(record)
    snippet, page = _best_evidence(record)

    breakdown = {
        "authority": _authority_points(record),
        "currency": _currency_points(record),
        "integration_breadth": min(4, len(positive)),
        "operational_specificity": min(3, len(operationalized)),
        "traceability": (1 if snippet else 0) + (1 if page not in ("", None) and page != 0 else 0),
        "novelty": (1 if "C" in positive else 0)
        + (1 if str(record.get("country") or record.get("reference_country") or "").strip().lower() not in _COMMON_ANGLO and (record.get("country") or record.get("reference_country")) else 0),
        "implementation_material": (1 if "implementation:" in str(record.get("themes_present") or "") else 0)
        + (1 if operationalized else 0),
    }
    total = min(18, sum(breakdown.values()))
    return {"gem_score": total, "breakdown": breakdown, "source_snippet": snippet, "source_page": page,
            "domains_covered": "".join(positive)}


def _manuscript_section(breakdown: dict, positive: list[str]) -> str:
    if breakdown["integration_breadth"] >= 3:
        return "results / matriz de integração"
    if breakdown["operational_specificity"] >= 2 or breakdown["implementation_material"] >= 1:
        return "discussão / implementação"
    if breakdown["novelty"] >= 1:
        return "introdução / contexto"
    return "resultados"


def gem_row(record: dict) -> dict:
    """Build one reviewable gem row for a record (assistive; human approves)."""
    scored = score_gem(record)
    positive = _positive_domains(record)
    return {
        "name": record.get("name", ""),
        "country": record.get("country", record.get("reference_country", "")),
        "doc_type": record.get("doc_type", ""),
        "gem_score": scored["gem_score"],
        "domains_covered": scored["domains_covered"],
        "n_domains_covered": len(positive),
        "source_snippet": scored["source_snippet"],
        "source_page": scored["source_page"],
        "proposed_claim": "",  # a human writes the paraphrase — never fabricated
        "manuscript_section": _manuscript_section(scored["breakdown"], positive),
        "why_it_matters": "; ".join(f"{k}={v}" for k, v in scored["breakdown"].items() if v),
        "score_breakdown": json.dumps(scored["breakdown"], ensure_ascii=False),
        "reference": record.get("reference", ""),
        "limitations": "valor descritivo — NÃO é avaliação de qualidade/risco de viés",
        "status": "candidate",
        "needs_human_review": True,
    }


def rank_gems(rows: list[dict], *, min_score: int = 1) -> list[dict]:
    """Return gem rows scored and ranked (highest first), filtered by min_score."""
    gems = [gem_row(r) for r in rows]
    gems = [g for g in gems if g["gem_score"] >= min_score]
    gems.sort(key=lambda g: g["gem_score"], reverse=True)
    for i, gem in enumerate(gems, start=1):
        gem["rank"] = i
    return gems


def best_gems_markdown(gems: list[dict], *, top: int = 20) -> str:
    """A human-readable 'best gems' brief (top N) for the manuscript."""
    lines = ["# Evidence Gems — melhores riquezas (candidatas, revisão humana)\n",
             "> Valor **descritivo** para o Artigo 1 — NÃO é avaliação de qualidade ou risco de viés.\n"]
    for gem in gems[:top]:
        lines.append(f"## {gem['rank']}. {gem['name']} ({gem['country']}) — score {gem['gem_score']}/18")
        lines.append(f"- **Domínios:** {gem['domains_covered'] or '—'}  ·  **Destino:** {gem['manuscript_section']}")
        if gem["source_snippet"]:
            page = gem["source_page"]
            loc = f" (p.{page})" if page not in ("", None, 0) else ""
            lines.append(f"- **Trecho{loc}:** \"{gem['source_snippet']}\"")
        if gem["reference"]:
            lines.append(f"- **Referência:** {gem['reference']}")
        lines.append(f"- **Por quê:** {gem['why_it_matters']}")
        lines.append("")
    return "\n".join(lines)
