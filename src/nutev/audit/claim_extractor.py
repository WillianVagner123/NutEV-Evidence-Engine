from __future__ import annotations

import hashlib
import re
from typing import Any

from nutev.audit.models import EvidenceClaim

RECOMMEND_TERMS = {"recommend","should","advise","limit","reduce","increase","consume","avoid","prefer","encourage","guideline","recomenda","deve","limitar","reduzir","aumentar","consumir","evitar","preferir"}
PROTOCOL_HINTS = {
    "diretrizes_dieteticas": ["guideline", "diretriz", "recommend", "recomenda"],
    "adesao_implementacao": ["adherence", "implement", "ades", "barrier"],
    "modificadores_clinicos": ["diabetes", "obesity", "hypertension", "cardio"],
}


def split_text_into_candidate_sentences(text: str) -> list[str]:
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def normalize_claim_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def build_claim_id(document_id: str, claim_text: str) -> str:
    digest = hashlib.sha1(f"{document_id}|{normalize_claim_text(claim_text).lower()}".encode()).hexdigest()[:16]  # noqa: S324
    return f"claim_{digest}"


def detect_claim_domains(sentence: str, ontology_or_domain_rules: dict) -> list[str]:
    s = sentence.lower()
    found: list[str] = []
    domains = (ontology_or_domain_rules or {}).get("domains", {})
    for domain, terms in domains.items():
        if any(str(t).lower() in s for t in terms):
            found.append(domain)
    if "ultra-processed" in s and "food_processing" not in found:
        found.append("food_processing")
    return sorted(set(found))


def detect_claim_protocol_components(sentence: str, ontology_or_rules: dict) -> list[str]:
    s = sentence.lower()
    out = []
    for comp, terms in PROTOCOL_HINTS.items():
        if any(t in s for t in terms):
            out.append(comp)
    return sorted(set(out))


def extract_candidate_claims_from_field(record: dict, field_name: str, ontology: dict | None, audit_rules: dict) -> list[EvidenceClaim]:
    field_text = str(record.get(field_name, "") or "").strip()
    if not field_text:
        return []
    out: list[EvidenceClaim] = []
    for sentence in split_text_into_candidate_sentences(field_text):
        norm = normalize_claim_text(sentence)
        domains = detect_claim_domains(norm, ontology or {})
        has_recommend = any(t in norm.lower() for t in RECOMMEND_TERMS)
        if not domains and not has_recommend:
            continue
        out.append(EvidenceClaim(
            claim_id=build_claim_id(str(record.get("document_id", "unknown")), norm),
            document_id=str(record.get("document_id", "")).strip(),
            run_id=record.get("run_id"),
            title=record.get("title"),
            source_url=record.get("url") or record.get("source_url"),
            source_type=record.get("source_type"),
            source_provider=record.get("source_provider") or record.get("source"),
            source_institution=record.get("source_institution"),
            country=record.get("country"),
            year=record.get("year"),
            claim_text=norm,
            exact_quote=sentence,
            quote_location=field_name,
            evidence_type=record.get("evidence_type", "extracted_quote"),
            nutev_domains=domains,
            clinical_conditions=record.get("clinical_conditions", []),
            dietary_patterns=record.get("diet_patterns", []),
            outcomes=record.get("outcomes", []),
            protocol_components=detect_claim_protocol_components(norm, ontology or {}),
            evidence_lenses=record.get("evidence_lenses", []),
            computational_confidence=0.7,
            claim_status="supported",
            needs_human_review=False,
        ))
    return out


def extract_candidate_claims_from_record(record: dict, ontology: dict | None, audit_rules: dict) -> list[EvidenceClaim]:
    claims: list[EvidenceClaim] = []
    for field_name in ["title", "abstract", "extracted_text"]:
        claims.extend(extract_candidate_claims_from_field(record, field_name, ontology, audit_rules))
    dedup: dict[str, EvidenceClaim] = {}
    for c in claims:
        key = f"{c.document_id}|{normalize_claim_text(c.claim_text).lower()}"
        if key not in dedup:
            dedup[key] = c
    if dedup:
        return list(dedup.values())
    return []
