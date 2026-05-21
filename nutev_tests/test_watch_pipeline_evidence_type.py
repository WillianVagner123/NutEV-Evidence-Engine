from nutev.global_watch.watch_pipeline import infer_evidence_type


def test_infer_evidence_type_recognizes_guidance_variants_as_guideline() -> None:
    titles = [
        "Standards of Care in Obesity and Cardiometabolic Risk",
        "Clinical Decision Pathway for MASLD Nutrition Care",
        "Joint Guideline on Dietary Management of Hypertension",
        "Practice Guidance for Adult Obesity Care",
    ]

    for title in titles:
        assert infer_evidence_type(title, "", "") == "guideline"


def test_infer_evidence_type_keeps_consensus_statement_as_consensus() -> None:
    title = "Expert Consensus Statement on Food Literacy and Lifestyle Medicine"

    assert infer_evidence_type(title, "", "") == "consensus"
