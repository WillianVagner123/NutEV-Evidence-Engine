from __future__ import annotations

import json
from pathlib import Path

from nutev.analysis.relevance import score_record


def _load_scoring_rules() -> dict:
    config_path = Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def test_scoring_rules_include_guidance_and_implementation_variants() -> None:
    keyword_points = _load_scoring_rules()["keyword_points"]

    expected_terms = [
        "implementation research",
        "implementation determinants",
        "implementation barriers",
        "implementation facilitators",
        "shared decision making",
        "behavior change technique",
        "self-management support",
        "dietary adherence",
        "treatment adherence",
        "practice guidance",
        "guidance statement",
        "clinical guidance",
        "guideline update",
        "clinical practice update",
        "best practice advice",
        "standards of care",
        "scientific advisory",
        "clinical pathway",
        "care pathway",
        "clinical decision pathway",
        "decision pathway",
    ]

    for term in expected_terms:
        assert term in keyword_points


def test_score_record_rewards_guidance_and_implementation_language() -> None:
    scoring_rules = _load_scoring_rules()
    base_record = {
        "title": "Nutrition management for adults with cardiometabolic risk",
        "abstract": "General review of dietary care in adults.",
        "journal": "Clinical Nutrition",
        "source": "pubmed",
        "url": "https://example.org/article",
    }
    targeted_record = {
        "title": (
            "Standards of Care and Best Practice Advice for MASLD and "
            "cardiometabolic risk"
        ),
        "abstract": (
            "This clinical guidance discusses implementation research, "
            "implementation determinants, shared decision making, self-management "
            "support and treatment adherence in adult care pathways."
        ),
        "journal": "Clinical Nutrition",
        "source": "pubmed",
        "url": "https://example.org/article",
    }

    base_score = score_record(dict(base_record), scoring_rules, "busca2a")["relevance_score"]
    targeted_score = score_record(dict(targeted_record), scoring_rules, "busca2a")["relevance_score"]

    assert targeted_score > base_score
    assert targeted_score - base_score >= 12
