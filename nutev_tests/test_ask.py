from __future__ import annotations

import json

from nutev.llm.ask import answer, build_context, load_corpus, retrieve
from nutev.llm.chat_client import get_chat_client

CORPUS = [
    {
        "document_id": "doc-medi",
        "title": "Mediterranean diet and type 2 diabetes in Brazil",
        "abstract": (
            "A randomized trial of the mediterranean diet pattern in Brazilian "
            "adults with diabetes, measuring glycemic outcomes."
        ),
        "year": 2021,
        "countries": ["Brazil"],
        "region": "Latin America",
        "journal": "Nutrition & Diabetes",
        "doi": "10.1000/medi",
        "url": "https://example.org/medi",
        "domains": ["nutrition"],
        "outcomes": ["glycemic control"],
        "diet_patterns": ["mediterranean diet"],
        "clinical_conditions": ["diabetes"],
        "relevance_score": 0.9,
        "cited_by_count": 12,
    },
    {
        "document_id": "doc-sleep",
        "title": "Sleep hygiene interventions for shift workers",
        "abstract": "A review of sleep hygiene programs and their effects.",
        "year": 2019,
        "countries": ["Canada"],
        "journal": "Sleep Science",
        "doi": "10.1000/sleep",
        "url": "https://example.org/sleep",
        "domains": ["sleep"],
        "outcomes": ["fatigue"],
        "diet_patterns": [],
        "clinical_conditions": [],
        "relevance_score": 0.4,
        "cited_by_count": 3,
    },
    {
        "document_id": "doc-urban",
        "title": "Urban transport policy and air quality",
        "abstract": "An analysis of transit policy effects on urban air pollution.",
        "year": 2020,
        "countries": ["Germany"],
        "journal": "Transport Policy",
        "doi": None,
        "url": None,
        "domains": ["environment"],
        "outcomes": ["air quality"],
        "relevance_score": 0.5,
        "cited_by_count": 7,
    },
]


def _write_corpus(tmp_path, records=CORPUS):
    path = tmp_path / "corpus.jsonl"
    lines = [json.dumps(rec, ensure_ascii=False) for rec in records]
    # Include a blank line and a malformed line to exercise defensive parsing.
    path.write_text("\n".join(lines) + "\n\nnot-json\n", encoding="utf-8")
    return tmp_path


class FakeClient:
    def chat(self, system: str, user: str) -> str:
        assert "SOURCES:" in user
        return "FAKE answer grounded in [1]"


def test_retrieve_ranks_on_topic_doc_first(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    records = load_corpus(_write_corpus(tmp_path))
    hits = retrieve(records, "mediterranean diet diabetes", k=3)
    assert hits[0]["document_id"] == "doc-medi"
    assert hits[0]["_retrieval_score"] > 0


def test_retrieve_handles_unicode_query(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    records = load_corpus(_write_corpus(tmp_path))
    # Portuguese token with accented characters must not raise.
    hits = retrieve(records, "alimentação saudável diabetes", k=3)
    assert isinstance(hits, list)
    assert len(hits) == 3


def test_load_corpus_missing_file_returns_empty(tmp_path):
    assert load_corpus(tmp_path) == []


def test_answer_offline_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    kb_dir = _write_corpus(tmp_path)
    result = answer("mediterranean diet diabetes", kb_dir, k=3, client="auto")

    assert result["mode"] == "offline"
    assert result["backend"] == "offline"
    assert result["answer"].strip()
    assert result["n_corpus"] == len(CORPUS)
    assert result["citations"]
    top_ids = [c["document_id"] for c in result["citations"]]
    assert "doc-medi" in top_ids
    assert result["citations"][0]["index"] == 1


def test_answer_with_injected_client(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    kb_dir = _write_corpus(tmp_path)
    result = answer("mediterranean diet", kb_dir, k=2, client=FakeClient())

    assert result["mode"] == "llm"
    assert "FAKE" in result["answer"]
    assert result["citations"]


def test_get_chat_client_offline(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "should-be-ignored")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "should-be-ignored")
    assert get_chat_client() is None


def test_build_context_truncates_and_numbers(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    records = load_corpus(_write_corpus(tmp_path))
    hits = retrieve(records, "mediterranean diet diabetes", k=3)
    context = build_context(hits)
    assert context.startswith("[1] ")
    assert "[2] " in context
