from __future__ import annotations

import json
from pathlib import Path


def test_article1_active_method_is_critical_review_and_legacy_search_is_historical() -> None:
    root = Path(__file__).resolve().parents[1]
    method = json.loads((root / "config/nutev/article1_method_master_v2.json").read_text(encoding="utf-8"))

    assert method["master_type"] == "NUTEV_ARTICLE1_METHOD_MASTER"
    assert method["active_for_current_article1"] is True
    assert method["study_type"] == "CRITICAL_STRUCTURED_REVIEW"
    assert method["status"] == "OWNER_APPROVED_ADVISOR_CONFIRMATION_PENDING"

    design = method["method"]
    assert design["dual_independent_screening_required"] is False
    assert design["prisma_scr_applicable"] is False
    assert design["formal_prisma_event_applicable"] is False
    assert design["exhaustive_mapping_claimed"] is False
    assert design["selection_register_required"] is True

    legacy = method["legacy_scoping_program"]
    assert legacy["status"] == "HISTORICAL_SUPERSEDED_NOT_DELETED"
    assert legacy["classification"] == "PILOT_SEARCH_PRE_PRESS_NOT_PRISMA"
    assert legacy["press_transferable_to_current_method"] is False
    assert (root / legacy["search_master"]).is_file()

    guardrails = method["guardrails"]
    assert guardrails["do_not_delete_legacy_artifacts"] is True
    assert guardrails["do_not_require_r1_r2_for_active_method"] is True
    assert guardrails["do_not_emit_prisma_for_active_method"] is True
    assert guardrails["do_not_claim_nutev_validation"] is True
