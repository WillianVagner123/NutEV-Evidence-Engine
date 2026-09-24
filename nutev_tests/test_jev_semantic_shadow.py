from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import requests


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "jev_semantic_shadow.py"
SPEC = importlib.util.spec_from_file_location("jev_semantic_shadow", MODULE_PATH)
assert SPEC and SPEC.loader
jev = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = jev
SPEC.loader.exec_module(jev)


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        if self.error:
            raise self.error
        assert self.response is not None
        return self.response


def config(mode: str = "shadow") -> jev.JevConfig:
    return jev.JevConfig(
        mode=mode,
        api_key="test-key",
        base_url="https://api.typesafe.ai",
        model="jev-test",
        timeout_seconds=1.0,
        limit=10,
    )


def ranked_row() -> dict:
    return {
        "reference_rank": 1,
        "reference_score": 88.0,
        "reference_tier": "A_TOP_REFERENCE",
        "title": "Dietary patterns and cardiometabolic health",
        "abstract": "A randomized trial evaluating dietary patterns.",
        "keywords": ["diet", "cardiometabolic"],
        "article_type": "journal article",
        "reference_year": 2025,
        "reference_provider": "pubmed",
        "pmid": "12345678",
        "human_eligibility": "include",
        "prisma_decision": "included",
        "private_workspace_id": "workspace-secret",
    }


def test_semantic_state_excludes_ranking_and_scientific_decisions() -> None:
    state = jev.semantic_state(ranked_row())
    serialized = json.dumps(state)

    assert "reference_score" not in state
    assert "reference_tier" not in state
    assert "human_eligibility" not in state
    assert "prisma_decision" not in state
    assert "private_workspace_id" not in state
    assert "12345678" not in serialized
    assert state["title"] == "Dietary patterns and cardiometabolic health"


def test_off_mode_never_calls_provider() -> None:
    session = FakeSession(error=AssertionError("must not call provider"))
    result = jev.evaluate_record(ranked_row(), config("off"), session=session)
    assert result["status"] == "disabled"
    assert result["ranking_effect"] == "none"
    assert result["scientific_effect"] == "none"
    assert session.calls == []


def test_shadow_normalizes_semantic_metadata_only() -> None:
    response = FakeResponse(
        {
            "model": "jev-test",
            "answers": {
                "document_type": {
                    "type": "choice",
                    "choice": "randomized_trial",
                    "confidence": 0.94,
                    "probabilities": {
                        "randomized_trial": 0.94,
                        "other": 0.06,
                    },
                },
                "nutrition_relevance": {
                    "type": "score",
                    "score": 3.8,
                    "confidence": 0.89,
                    "legend": {},
                    "probabilities": {"3": 0.2, "4": 0.8},
                },
                "semantic_ambiguity": {
                    "type": "noul",
                    "noul": 0.08,
                },
            },
            "usage": {"input_tokens": 120, "output_tokens": 12},
        }
    )
    session = FakeSession(response=response)

    result = jev.evaluate_record(ranked_row(), config(), session=session)

    assert result["status"] == "ok"
    assert result["document_type"] == "randomized_trial"
    assert result["nutrition_relevance_score"] == 3.8
    assert result["semantic_ambiguity_probability"] == 0.08
    assert result["ranking_effect"] == "none"
    assert result["scientific_effect"] == "none"

    sent = session.calls[0]["json"]
    assert "reference_score" not in sent["state"]
    assert "prisma_decision" not in sent["state"]


def test_provider_failure_is_recorded_without_scientific_effect() -> None:
    session = FakeSession(error=requests.ConnectionError("offline"))
    result = jev.evaluate_record(ranked_row(), config(), session=session)
    assert result["status"] == "network_error"
    assert result["ranking_effect"] == "none"
    assert result["scientific_effect"] == "none"


def test_run_writes_separate_artifacts_and_preserves_ranking(tmp_path: Path) -> None:
    ranking = tmp_path / "reference_ranking.jsonl"
    ranking.write_text(json.dumps(ranked_row()) + "\n", encoding="utf-8")
    before = ranking.read_bytes()

    output = tmp_path / "shadow"
    session = FakeSession(
        response=FakeResponse(
            {
                "model": "jev-test",
                "answers": {
                    "document_type": {
                        "choice": "randomized_trial",
                        "confidence": 0.9,
                        "probabilities": {"randomized_trial": 0.9, "other": 0.1},
                    },
                    "nutrition_relevance": {
                        "score": 4.0,
                        "confidence": 0.9,
                        "probabilities": {"4": 1.0},
                    },
                    "semantic_ambiguity": {"noul": 0.05},
                },
                "usage": {"input_tokens": 10, "output_tokens": 3},
            }
        )
    )

    manifest = jev.run(ranking, output, config(), session=session)

    assert ranking.read_bytes() == before
    assert manifest["ranking_effect"] == "none"
    assert manifest["scientific_effect"] == "none"
    assert (output / "semantic_shadow.jsonl").is_file()
    assert (output / "JEV_SHADOW_MANIFEST.json").is_file()
