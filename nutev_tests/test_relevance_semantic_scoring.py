from __future__ import annotations

import json
from pathlib import Path

from nutev.analysis.relevance import score_record


BASE_SCORING_RULES = {
    "keyword_points": {
        "implementation science": 3,
        "implementation fidelity": 2,
        "knowledge translation": 2,
        "mind diet": 2,
        "food agency": 3,
        "masld": 2,
        "steatotic liver disease": 2,
        "food-based dietary guideline": 4,
        "nutrition counselling": 3,
    },
    "source_points": {"pubmed": 3, "official": 4},
    "workstream_points": {"busca1": 2, "busca2a": 3, "busca2b": 3},
    "editorial_authority_points": {},
}


def test_busca2b_semantic_terms_raise_relevance_score() -> None:
    baseline = {
        "title": "Obesity trial in adults",
        "abstract": "Adults with obesity were followed prospectively.",
        "url": "https://example.org/article",
        "source": "pubmed",
    }
    enriched = {
        "title": (
            "Implementation science, knowledge translation and food agency "
            "in a MIND diet trial for obesity and MASLD"
        ),
        "abstract": (
            "Behavior change support and implementation fidelity were "
            "evaluated in adults with steatotic liver disease."
        ),
        "url": "https://example.org/full-text.pdf",
        "source": "pubmed",
    }

    base_score = score_record(dict(baseline), BASE_SCORING_RULES, "busca2b")
    enriched_score = score_record(dict(enriched), BASE_SCORING_RULES, "busca2b")

    assert enriched_score["relevance_score"] > base_score["relevance_score"] + 20
    assert enriched_score["out_of_scope_flags"] == []


def test_busca1_guideline_and_counselling_terms_are_prioritized() -> None:
    neutral = {
        "title": "Community obesity nutrition article",
        "abstract": "Adults discussed healthy diet choices.",
        "url": "https://example.org/article",
        "source": "official",
    }
    targeted = {
        "title": "Food-based dietary guideline for adult obesity prevention",
        "abstract": (
            "The report covers nutrition counselling, food literacy and "
            "shared meals in community adults."
        ),
        "url": "https://example.org/guideline.pdf",
        "source": "official",
    }

    neutral_score = score_record(dict(neutral), BASE_SCORING_RULES, "busca1")
    targeted_score = score_record(dict(targeted), BASE_SCORING_RULES, "busca1")

    assert targeted_score["relevance_score"] > neutral_score["relevance_score"] + 15
    assert targeted_score["out_of_scope_flags"] == []


def test_busca2a_guidance_statement_and_decision_pathway_are_prioritized() -> None:
    baseline = {
        "title": "Adult obesity care update",
        "abstract": "Adults with obesity received routine nutrition follow-up.",
        "url": "https://example.org/update",
        "source": "official",
    }
    targeted = {
        "title": (
            "Joint statement and clinical decision pathway for obesity, "
            "dyslipidemia and cardiometabolic risk"
        ),
        "abstract": (
            "This practice guidance summarizes therapeutic lifestyle changes, "
            "medical nutrition therapy and blood pressure management in adults."
        ),
        "url": "https://example.org/guidance.pdf",
        "source": "official",
    }

    baseline_score = score_record(dict(baseline), BASE_SCORING_RULES, "busca2a")
    targeted_score = score_record(dict(targeted), BASE_SCORING_RULES, "busca2a")

    assert targeted_score["relevance_score"] > baseline_score["relevance_score"] + 25
    assert targeted_score["out_of_scope_flags"] == []


def test_busca2b_lipid_risk_terms_raise_relevance_score() -> None:
    baseline = {
        "title": "Adult nutrition follow-up",
        "abstract": "Adults received standard lifestyle advice.",
        "url": "https://example.org/article",
        "source": "pubmed",
    }
    enriched = {
        "title": "Hyperlipidemia and hypercholesterolemia dietary intervention trial",
        "abstract": (
            "Adults with cardiometabolic risk and dyslipidaemia completed a "
            "Mediterranean diet adherence program."
        ),
        "url": "https://example.org/full-text.pdf",
        "source": "pubmed",
    }

    base_score = score_record(dict(baseline), BASE_SCORING_RULES, "busca2b")
    enriched_score = score_record(dict(enriched), BASE_SCORING_RULES, "busca2b")

    assert enriched_score["relevance_score"] > base_score["relevance_score"] + 20
    assert enriched_score["out_of_scope_flags"] == []


def test_busca2b_dietitian_led_medical_nutrition_therapy_is_prioritized() -> None:
    baseline = {
        "title": "Adult obesity nutrition follow-up",
        "abstract": "Adults received dietary advice during follow-up.",
        "url": "https://example.org/article",
        "source": "pubmed",
    }
    enriched = {
        "title": (
            "Registered dietitian nutritionist-led medical nutrition therapy "
            "trial for obesity and type 2 diabetes"
        ),
        "abstract": (
            "A dietitian-led intervention evaluated adherence, glycemic "
            "control and cardiometabolic outcomes in adults."
        ),
        "url": "https://example.org/full-text.pdf",
        "source": "pubmed",
    }

    base_score = score_record(dict(baseline), BASE_SCORING_RULES, "busca2b")
    enriched_score = score_record(dict(enriched), BASE_SCORING_RULES, "busca2b")

    assert enriched_score["relevance_score"] > base_score["relevance_score"] + 18
    assert enriched_score["out_of_scope_flags"] == []


def test_busca2b_behavior_change_taxonomy_variants_raise_relevance_score() -> None:
    baseline = {
        "title": "Adult obesity implementation follow-up",
        "abstract": "Adults received routine diet support during follow-up.",
        "url": "https://example.org/article",
        "source": "pubmed",
    }
    enriched = {
        "title": (
            "Implementation outcomes framework and behaviour change techniques "
            "for obesity care delivery"
        ),
        "abstract": (
            "A COM B implementation mapping study evaluated food agency, "
            "adherence and cardiometabolic outcomes in adults."
        ),
        "url": "https://example.org/full-text.pdf",
        "source": "pubmed",
    }

    baseline_score = score_record(dict(baseline), BASE_SCORING_RULES, "busca2b")
    enriched_score = score_record(dict(enriched), BASE_SCORING_RULES, "busca2b")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 18
    assert enriched_score["out_of_scope_flags"] == []


def test_busca2b_time_restricted_eating_variants_are_prioritized() -> None:
    scoring_rules = json.loads(
        (Path(__file__).resolve().parents[1] / "config" / "scoring_rules.json").read_text(
            encoding="utf-8"
        )
    )
    baseline = {
        "title": "Lifestyle intervention for obesity and MASLD",
        "abstract": "Adults received dietary advice with weight follow-up.",
        "url": "https://example.org/article",
        "source": "pubmed",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": (
            "Early time-restricted feeding and intermittent fasting trial for "
            "obesity and MASLD"
        ),
        "abstract": (
            "Adults with cardiometabolic risk completed a time restricted "
            "eating intervention with metabolic follow-up."
        ),
        "url": "https://example.org/full-text.pdf",
        "source": "pubmed",
        "journal": "",
        "source_institution": "",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "busca2b")
    enriched_score = score_record(dict(enriched), scoring_rules, "busca2b")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 12
    assert enriched_score["out_of_scope_flags"] == []