#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "apps" / "nutev-web" / "agent-context" / "article1"
CONTEXT_VERSION = "nutev_predeploy_browser_fixture_v1"
SEARCH_ID = "predeploy_browser_fixture"


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)

    articles = [
        {
            "context_version": CONTEXT_VERSION,
            "document_id": "fixture-guideline-001",
            "title": "Food-based dietary guideline implementation fixture",
            "year": 2024,
            "doi": "10.0000/nutev.fixture.001",
            "pmid": None,
            "source_provider": "pubmed",
            "document_class": "food_based_dietary_guideline",
            "full_text_status": "retrieved",
            "reference_stub": "Deterministic browser fixture; not scientific evidence.",
            "routes": ["B-NORM"],
            "review_profile": {
                "profile_version": "fixture-v1",
                "primary_document_class": "food_based_dietary_guideline",
                "document_classification_basis": "deterministic_test_fixture",
                "document_class_confidence": "high",
                "document_class_matches": {},
                "document_class_warnings": ["test fixture only"],
                "operational_domains": ["food_based_guidance", "implementation_practice"],
                "operational_domain_matches": {},
            },
            "evidence_excerpt_count": 0,
            "result_bundle_count": 0,
            "guardrail": "PRE-DEPLOY UI FIXTURE ONLY; not eligibility, evidence, quality, certainty or PRISMA.",
        },
        {
            "context_version": CONTEXT_VERSION,
            "document_id": "fixture-observational-002",
            "title": "Nutrition assessment observational fixture",
            "year": 2022,
            "doi": None,
            "pmid": "00000002",
            "source_provider": "europepmc",
            "document_class": "primary_observational",
            "full_text_status": "partial",
            "reference_stub": "Deterministic browser fixture; not scientific evidence.",
            "routes": ["C-STRUCT"],
            "review_profile": {
                "profile_version": "fixture-v1",
                "primary_document_class": "primary_observational",
                "document_classification_basis": "deterministic_test_fixture",
                "document_class_confidence": "high",
                "document_class_matches": {},
                "document_class_warnings": ["test fixture only"],
                "operational_domains": ["nutrition_assessment", "social_context"],
                "operational_domain_matches": {},
            },
            "evidence_excerpt_count": 0,
            "result_bundle_count": 0,
            "guardrail": "PRE-DEPLOY UI FIXTURE ONLY; not eligibility, evidence, quality, certainty or PRISMA.",
        },
        {
            "context_version": CONTEXT_VERSION,
            "document_id": "fixture-review-003",
            "title": "Dietary counseling evidence synthesis fixture",
            "year": 2025,
            "doi": "10.0000/nutev.fixture.003",
            "pmid": "00000003",
            "source_provider": "openalex",
            "document_class": "evidence_synthesis",
            "full_text_status": "retrieved",
            "reference_stub": "Deterministic browser fixture; not scientific evidence.",
            "routes": ["B-NORM", "C-STRUCT"],
            "review_profile": {
                "profile_version": "fixture-v1",
                "primary_document_class": "evidence_synthesis",
                "document_classification_basis": "deterministic_test_fixture",
                "document_class_confidence": "high",
                "document_class_matches": {},
                "document_class_warnings": ["test fixture only"],
                "operational_domains": ["dietary_counseling", "monitoring_follow_up"],
                "operational_domain_matches": {},
            },
            "evidence_excerpt_count": 0,
            "result_bundle_count": 0,
            "guardrail": "PRE-DEPLOY UI FIXTURE ONLY; not eligibility, evidence, quality, certainty or PRISMA.",
        },
    ]

    state = {
        "context_version": CONTEXT_VERSION,
        "created_at": "2000-01-01T00:00:00+00:00",
        "search_id": SEARCH_ID,
        "question": "Deterministic pre-deploy browser fixture — not a scientific question",
        "master_status": "TEST_FIXTURE_ONLY",
        "formal_search": {
            "press_status": "PENDING",
            "gf10_authorized": False,
            "query_freeze_complete": False,
            "formal_provider_search_executed": False,
            "prisma_search_event_emitted": False,
            "next_gate": "Browser E2E only",
        },
        "runtime": {
            "workbench": {"status": "PASS", "counts": {"articles": 3}, "database_sha256": "fixture"},
            "deepening": {
                "present": True,
                "status": "COMPLETE",
                "counts": {"tier_records": 3},
                "retrieval_status_counts": {"retrieved": 2, "partial": 1},
                "extraction_method_counts": {"fixture": 3},
            },
            "review_profiles": {"present": True, "status": "PASS", "profile_version": "fixture-v1", "counts": {"articles": 3}},
            "article1_routes": {
                "status": "PASS",
                "queue_version": "fixture-v1",
                "counts": {
                    "tier_records": 3,
                    "B-NORM": 2,
                    "C-STRUCT": 2,
                    "route_union_documents": 3,
                    "route_overlap_documents": 1,
                    "unrouted_documents": 0,
                },
                "manifest_sha256": "fixture",
            },
            "vocabulary_audit": {"present": False, "status": None, "audit_version": None},
            "agent_article_summaries": 3,
        },
        "guardrails": {
            "discovery_is_not_formal_prisma_search": True,
            "agent_summaries_are_rank_blind": True,
            "agent_summaries_contain_full_text": False,
            "agent_summaries_are_not_screening_decisions": True,
            "formal_gate_is_not_changed_by_context_build": True,
            "test_fixture_only": True,
        },
    }

    manifest = {
        "schema_version": 1,
        "context_type": "NUTEV_ARTICLE1_AGENT_CONTEXT",
        "context_version": CONTEXT_VERSION,
        "status": "PASS",
        "created_at": "2000-01-01T00:00:00+00:00",
        "search_id": SEARCH_ID,
        "source": {"fixture": True},
        "counts": {
            "article_summaries": 3,
            "document_class_counts": {
                "evidence_synthesis": 1,
                "food_based_dietary_guideline": 1,
                "primary_observational": 1,
            },
            "route_counts": {"B-NORM": 2, "C-STRUCT": 2},
        },
        "outputs": {},
        "safety": {
            "rank_blind": True,
            "full_text_included": False,
            "eligibility_decisions_included": False,
            "prisma_events_included": False,
            "external_llm_calls": 0,
            "test_fixture_only": True,
        },
    }

    write_json(DESTINATION / "SEARCH_STATE.json", state)
    write_json(DESTINATION / "CONTEXT_MANIFEST.json", manifest)
    (DESTINATION / "SEARCH_SUMMARY.md").write_text(
        "# PRE-DEPLOY BROWSER FIXTURE\n\nThis file is deterministic UI test data only; it is not scientific evidence.\n",
        encoding="utf-8",
    )
    with (DESTINATION / "ARTICLE_SUMMARIES.jsonl").open("w", encoding="utf-8") as handle:
        for article in articles:
            handle.write(json.dumps(article, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"materialized deterministic browser context at {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
