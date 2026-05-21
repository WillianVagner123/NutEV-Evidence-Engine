from __future__ import annotations

from typing import Any


def _text_blob(record: dict[str, Any]) -> str:
    return " ".join(
        str(record.get(k, "") or "") for k in ("title", "abstract", "extracted_text")
    ).lower()


def _match_terms(blob: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term.lower() in blob)


def classify_evidence(
    records: list[dict[str, Any]],
    ontology: dict[str, Any],
    lenses_cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    domains = ontology.get("domains", {})
    outcomes = ontology.get("outcomes", {})
    lens_map = lenses_cfg.get("lenses", {})

    for r in records:
        blob = _text_blob(r)
        matched_domains: list[str] = []
        matched_outcomes: list[str] = []
        lens_scores: dict[str, int] = {}

        for domain, terms in domains.items():
            score = _match_terms(blob, terms)
            r[f"domain_{domain}_count"] = score
            r[f"domain_{domain}_present"] = int(score > 0)
            if score > 0:
                matched_domains.append(domain)

        for outcome, terms in outcomes.items():
            score = _match_terms(blob, terms)
            r[f"outcome_{outcome}_count"] = score
            r[f"outcome_{outcome}_present"] = int(score > 0)
            if score > 0:
                matched_outcomes.append(outcome)

        for lens, lens_cfg in lens_map.items():
            lens_domains = lens_cfg.get("domains", [])
            score = sum(int(d in matched_domains) for d in lens_domains)
            lens_scores[lens] = score
            r[f"lens_{lens}_score"] = score
            r[f"lens_{lens}_present"] = int(score > 0)

        r["domains"] = sorted(set(matched_domains))
        r["outcomes"] = sorted(set(matched_outcomes))
        r["evidence_lenses"] = [k for k, v in lens_scores.items() if v > 0]

    return records
