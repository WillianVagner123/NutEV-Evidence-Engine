from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = REPO_ROOT / "apps" / "nutev-web"
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

from nutev.registry.ingest import SearchRegistryIngestor
from nutev.search.base import ProviderResult

import progress_search
from query_compiler import compile_query_plan


QUESTION = "protein during weight loss in adults with obesity"
EXACT_QUERY = (
    '("Dietary Proteins"[Mesh] OR protein[Title/Abstract]) '
    'AND ("Weight Loss"[Mesh] OR "weight loss"[Title/Abstract])'
)


def _shared_row(provider: str) -> dict[str, Any]:
    return {
        "title": "Shared pre-deploy article",
        "abstract": "Protein intake during weight loss in adults with obesity.",
        "doi": "10.5555/nutev-predeploy-shared",
        "pmid": "99900001",
        "source_provider": provider,
        "source": provider,
        "journal": "Synthetic Journal",
        "year": "2026",
    }


def _fake_score_rows(rows: list[dict[str, Any]], *, query: str | None = None) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        item = dict(row)
        item["reference_rank"] = index
        item["reference_score"] = 90.0
        item["query_relevance_score"] = 92.0
        item["nutev_priority_score"] = 82.0
        ranked.append(item)
    return ranked


def _complete_provider_call(provider: str, query: str, _limit: int):
    return lambda: ProviderResult(
        provider,
        query,
        rows=[_shared_row(provider)],
        total_found=1,
        total_returned=1,
        status="completed",
    )


def _pubmed_details(query: str) -> dict[str, Any]:
    return {
        "search_details_complete": True,
        "errors_present": False,
        "count": 1,
        "query_translation": query,
        "warninglist": {},
        "errorlist": {},
    }


def _provider_queries(plan: dict[str, Any]) -> dict[str, str]:
    return {
        provider: str(value.get("query") or "")
        for provider, value in (plan.get("provider_queries") or {}).items()
        if isinstance(value, dict)
    }


def _advanced_strategy(framework: str) -> dict[str, Any]:
    concepts_by_framework = {
        "PCC": [
            {"label": "Population", "terms": ["free:adults", "mesh:Obesity"]},
            {"label": "Concept", "terms": ["free:protein", "decs:Proteínas"]},
            {"label": "Context", "terms": ["free:weight loss"]},
        ],
        "PICO": [
            {"label": "Population", "terms": ["free:adults", "mesh:Obesity"]},
            {"label": "Intervention", "terms": ["free:higher protein"]},
            {"label": "Comparator", "terms": ["free:standard protein"]},
            {"label": "Outcome", "terms": ["free:lean mass"]},
        ],
        "PECO": [
            {"label": "Population", "terms": ["free:adults", "mesh:Obesity"]},
            {"label": "Exposure", "terms": ["free:protein intake"]},
            {"label": "Comparator", "terms": ["free:lower protein"]},
            {"label": "Outcome", "terms": ["free:fat free mass"]},
        ],
    }
    return {"framework": framework, "concepts": concepts_by_framework[framework]}


def _registry(root: Path) -> SearchRegistryIngestor:
    registry_root = root / "registry"
    return SearchRegistryIngestor(
        registry_root / "article_registry.sqlite",
        registry_root / "ARTICLE_REGISTRY_MANIFEST.json",
    )


@pytest.mark.parametrize(
    ("label", "strategy", "global_search", "expected_mode", "expected_plan_mode"),
    [
        ("quick-bounded", None, False, "interactive_bounded", "natural_language"),
        ("quick-global", None, True, "global_exhaustive", "natural_language"),
        ("pcc-bounded", _advanced_strategy("PCC"), False, "structured_review_bounded", "structured_review"),
        ("pcc-global", _advanced_strategy("PCC"), True, "structured_review_global_exhaustive", "structured_review"),
        ("pico-bounded", _advanced_strategy("PICO"), False, "structured_review_bounded", "structured_review"),
        ("pico-global", _advanced_strategy("PICO"), True, "structured_review_global_exhaustive", "structured_review"),
        ("peco-bounded", _advanced_strategy("PECO"), False, "structured_review_bounded", "structured_review"),
        ("peco-global", _advanced_strategy("PECO"), True, "structured_review_global_exhaustive", "structured_review"),
        (
            "exact-bounded",
            {
                "mode": "exact",
                "strategy_id": "predeploy-protein-weight-loss",
                "strategy_version": "v1.0",
                "run_class": "DEVELOPMENT",
                "provider_queries": {"pubmed": EXACT_QUERY},
            },
            False,
            "exact_review_bounded",
            "exact_review",
        ),
        (
            "exact-global",
            {
                "mode": "exact",
                "strategy_id": "predeploy-protein-weight-loss",
                "strategy_version": "v1.0",
                "run_class": "DEVELOPMENT",
                "provider_queries": {"pubmed": EXACT_QUERY},
            },
            True,
            "exact_review_global_exhaustive",
            "exact_review",
        ),
    ],
)
def test_predeploy_search_mode_matrix_persists_through_registry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    label: str,
    strategy: dict[str, Any] | None,
    global_search: bool,
    expected_mode: str,
    expected_plan_mode: str,
) -> None:
    monkeypatch.setenv("NUTEV_SEARCH_FULLTEXT_LIMIT", "0")
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(progress_search, "_provider_call", _complete_provider_call)
    monkeypatch.setattr(progress_search, "_score_rows", _fake_score_rows)
    monkeypatch.setattr(progress_search, "collect_pubmed_search_details", _pubmed_details)

    providers = ["pubmed"]
    plan = compile_query_plan(QUESTION, providers, strategy)
    query_strings = _provider_queries(plan)

    result = progress_search.search_evidence_progressive(
        QUESTION,
        providers=providers,
        per_provider=0 if global_search else 25,
        max_results=0 if global_search else 100,
        provider_queries=query_strings,
        query_plan=plan,
        output_root=tmp_path,
    )

    assert result["search_mode"] == expected_mode, label
    assert result["query_plan"]["mode"] == expected_plan_mode, label
    assert result["status"] == "COMPLETE", label
    assert result["registry_summary"]["status"] == "COMPLETE", label
    assert result["results"][0]["article_id"].startswith("NUTEV-ART-"), label
    assert result["providers"][0]["provider_query"] == query_strings["pubmed"], label
    assert result["providers"][0]["query_dialect"] == plan["provider_queries"]["pubmed"]["dialect"], label

    if expected_plan_mode == "exact_review":
        assert plan["provider_queries"]["pubmed"]["query"] == EXACT_QUERY
        assert result["providers"][0]["provider_query"] == EXACT_QUERY
        assert result["query_plan"]["strategy_id"] == "predeploy-protein-weight-loss"
        assert result["query_plan"]["strategy_version"] == "v1.0"


def test_all_ten_modes_converge_on_one_article_identity(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("NUTEV_SEARCH_FULLTEXT_LIMIT", "0")
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(progress_search, "_provider_call", _complete_provider_call)
    monkeypatch.setattr(progress_search, "_score_rows", _fake_score_rows)
    monkeypatch.setattr(progress_search, "collect_pubmed_search_details", _pubmed_details)

    cases: list[tuple[dict[str, Any] | None, bool]] = [
        (None, False),
        (None, True),
        (_advanced_strategy("PCC"), False),
        (_advanced_strategy("PCC"), True),
        (_advanced_strategy("PICO"), False),
        (_advanced_strategy("PICO"), True),
        (_advanced_strategy("PECO"), False),
        (_advanced_strategy("PECO"), True),
        (
            {
                "mode": "exact",
                "strategy_id": "predeploy-protein-weight-loss",
                "strategy_version": "v1.0",
                "run_class": "DEVELOPMENT",
                "provider_queries": {"pubmed": EXACT_QUERY},
            },
            False,
        ),
        (
            {
                "mode": "exact",
                "strategy_id": "predeploy-protein-weight-loss",
                "strategy_version": "v1.0",
                "run_class": "DEVELOPMENT",
                "provider_queries": {"pubmed": EXACT_QUERY},
            },
            True,
        ),
    ]

    article_ids: list[str] = []
    search_ids: list[str] = []
    for strategy, global_search in cases:
        plan = compile_query_plan(QUESTION, ["pubmed"], strategy)
        result = progress_search.search_evidence_progressive(
            QUESTION,
            providers=["pubmed"],
            per_provider=0 if global_search else 25,
            max_results=0 if global_search else 100,
            provider_queries=_provider_queries(plan),
            query_plan=plan,
            output_root=tmp_path,
        )
        article_ids.append(str(result["results"][0]["article_id"]))
        search_ids.append(str(result["search_id"]))

    assert len(set(article_ids)) == 1
    assert len(set(search_ids)) == 10

    stats = _registry(tmp_path).stats()
    assert stats.articles == 1
    assert stats.search_runs == 10
    assert stats.search_hits == 10


def _run_gap_case(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    provider_status: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    monkeypatch.setenv("NUTEV_SEARCH_FULLTEXT_LIMIT", "0")
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)
    monkeypatch.setattr(progress_search, "_score_rows", _fake_score_rows)

    def provider_call(provider: str, query: str, _limit: int):
        return lambda: ProviderResult(
            provider,
            query,
            rows=rows,
            total_found=None,
            total_returned=len(rows),
            status=provider_status,
            error=f"synthetic_{provider_status}",
        )

    monkeypatch.setattr(progress_search, "_provider_call", provider_call)
    plan = compile_query_plan(QUESTION, ["brave"], None)
    return progress_search.search_evidence_progressive(
        QUESTION,
        providers=["brave"],
        per_provider=25,
        max_results=100,
        provider_queries=_provider_queries(plan),
        query_plan=plan,
        output_root=tmp_path,
    )


def _stored_provider_gaps(root: Path, search_id: str) -> list[Any]:
    connection = sqlite3.connect(root / "registry" / "article_registry.sqlite")
    try:
        row = connection.execute(
            "SELECT provider_gaps_json FROM search_runs WHERE search_id = ?",
            (search_id,),
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    return list(json.loads(row[0]))


def test_bounded_partial_provider_cannot_be_reported_as_complete(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = _run_gap_case(
        monkeypatch,
        tmp_path,
        provider_status="partial",
        rows=[_shared_row("brave")],
    )

    assert result["status"] == "COMPLETE_WITH_PROVIDER_GAPS"
    assert result["partial_providers"] == ["brave"]
    assert "brave" in _stored_provider_gaps(tmp_path, str(result["search_id"]))


def test_bounded_skipped_provider_cannot_mean_zero_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = _run_gap_case(
        monkeypatch,
        tmp_path,
        provider_status="skipped",
        rows=[],
    )

    assert result["status"] == "COMPLETE_WITH_PROVIDER_GAPS"
    assert result["skipped_providers"] == ["brave"]
    assert "brave" in _stored_provider_gaps(tmp_path, str(result["search_id"]))
