from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_implementation_semantic_block_adds_core_implementation_science_terms() -> None:
    rendered = " ".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "implementation fidelity" in rendered
    assert "implementation facilitation" in rendered
    assert "implementation support" in rendered
    assert "implementation research" in rendered
    assert "implementation evaluation" in rendered
    assert "process evaluation" in rendered
    assert "implementation determinant" in rendered
    assert "implementation determinants" in rendered
    assert "implementation barriers" in rendered
    assert "implementation facilitators" in rendered
    assert "shared decision making" in rendered
    assert "motivational interviewing" in rendered
    assert "behavior change technique" in rendered
    assert "self-management support" in rendered
    assert "sustainability" in rendered
    assert "dissemination" in rendered
    assert "scale-up" in rendered
    assert "hybrid type 1" in rendered
    assert "theoretical domains framework" in rendered
    assert "real-world evidence" in rendered


def test_implementation_semantic_block_adds_document_level_terms() -> None:
    rendered = " ".join(
        semantic_terms("busca2b", field="document_terms", min_priority=4)
    ).lower()

    assert "implementation evaluation" in rendered
    assert "process evaluation" in rendered
    assert "dissemination study" in rendered
    assert "hybrid type 2" in rendered
    assert "real world evidence" in rendered


def test_evidence_synthesis_semantic_block_adds_guidance_and_pathway_terms() -> None:
    rendered = " ".join(
        semantic_terms("busca2a", field="document_terms", min_priority=5)
    ).lower()

    assert "guideline update" in rendered
    assert "clinical practice update" in rendered
    assert "living guideline" in rendered
    assert "standards of care" in rendered
    assert "standards of medical care" in rendered
    assert "standards of medical care in diabetes" in rendered
    assert "consensus report" in rendered
    assert "consensus guidance" in rendered
    assert "consensus update" in rendered
    assert "practice guidance" in rendered
    assert "guidance statement" in rendered
    assert "joint statement" in rendered
    assert "joint guideline" in rendered
    assert "clinical guidance" in rendered
    assert "clinical practice recommendation" in rendered
    assert "clinical practice recommendations" in rendered
    assert "scientific advisory" in rendered
    assert "policy statement" in rendered
    assert "nutrition practice guideline" in rendered
    assert "dietetic practice guideline" in rendered
    assert "best practice advice" in rendered
    assert "clinical decision pathway" in rendered
    assert "decision pathway" in rendered


def test_lifestyle_nutrition_semantic_block_adds_pattern_and_lifestyle_terms() -> None:
    rendered = " ".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "therapeutic lifestyle changes" in rendered
    assert "mediterranean dietary pattern" in rendered
    assert "dietary approaches to stop hypertension" in rendered
    assert "planetary health diet" in rendered
    assert "meal replacement" in rendered
    assert "total diet replacement" in rendered
    assert "very low energy diet" in rendered


def test_lifestyle_nutrition_semantic_block_adds_anti_inflammatory_terms() -> None:
    terms = " ".join(semantic_terms("busca2b", min_priority=4)).lower()
    document_terms = " ".join(
        semantic_terms("busca2b", field="document_terms", min_priority=4)
    ).lower()

    assert "anti-inflammatory diet" in terms
    assert "anti inflammatory dietary pattern" in terms
    assert "empirical dietary inflammatory pattern" in terms
    assert "pro-inflammatory dietary pattern" in terms
    assert "anti-inflammatory diet systematic review" in document_terms
    assert "dietary inflammatory index meta-analysis" in document_terms


def test_food_literacy_semantic_block_adds_culinary_training_and_labeling_terms() -> None:
    rendered = " ".join(semantic_terms("artigo3_framework", min_priority=5)).lower()

    assert "culinary nutrition" in rendered
    assert "teaching kitchen" in rendered
    assert "teaching kitchens" in rendered
    assert "home cooking" in rendered
    assert "meal preparation" in rendered
    assert "cooking confidence" in rendered
    assert "nutrition education" in rendered
    assert "nutrition label" in rendered
    assert "label reading" in rendered
    assert "front-of-pack" in rendered
    assert "front-of-pack labeling" in rendered


def test_food_literacy_semantic_block_adds_operational_budget_and_shopping_terms() -> None:
    terms = semantic_terms("artigo3_framework", min_priority=5)
    document_terms = semantic_terms(
        "artigo3_framework",
        field="document_terms",
        min_priority=5,
    )

    assert "shopping skills" in terms
    assert "healthy grocery shopping" in terms
    assert "food budgeting" in terms
    assert "food resource management" in terms
    assert "shopping skills scale" in document_terms
    assert "food budgeting scale" in document_terms
    assert "food resource management questionnaire" in document_terms
