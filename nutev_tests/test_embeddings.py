from __future__ import annotations

from nutev.llm import embeddings

RECORDS = [
    {
        "document_id": "doc-medi",
        "title": "Mediterranean diet and type 2 diabetes in Brazil",
        "abstract": "A randomized trial of the mediterranean diet pattern.",
        "journal": "Nutrition & Diabetes",
        "domains": ["nutrition"],
        "outcomes": ["glycemic control"],
        "diet_patterns": ["mediterranean diet"],
        "clinical_conditions": ["diabetes"],
    },
    {
        "document_id": "doc-sleep",
        "title": "Sleep hygiene interventions for shift workers",
        "abstract": "A review of sleep hygiene programs and their effects.",
        "journal": "Sleep Science",
    },
]


def test_is_available_false_when_network_disabled(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert embeddings.is_available() is False


def test_build_or_load_index_none_when_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert embeddings.build_or_load_index(RECORDS, tmp_path) is None
    # No artifacts should have been written when unavailable.
    assert not (tmp_path / "embeddings").exists()


def test_semantic_retrieve_none_when_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert (
        embeddings.semantic_retrieve(RECORDS, "mediterranean diet", tmp_path)
        is None
    )


def test_semantic_retrieve_none_on_empty_records(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert embeddings.semantic_retrieve([], "anything", tmp_path) is None


def test_doc_text_weights_title_and_includes_metadata():
    text = embeddings._doc_text(RECORDS[0])
    # Title repeated TITLE_WEIGHT times for up-weighting.
    assert text.count("Mediterranean diet and type 2 diabetes in Brazil") == (
        embeddings.TITLE_WEIGHT
    )
    assert "glycemic control" in text
    assert "Nutrition & Diabetes" in text
