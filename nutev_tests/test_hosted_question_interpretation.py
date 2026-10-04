"""Hosted search: question interpretation (A1) and history strategy restore (A10).

See docs/SEARCH_KEYWORD_AUDIT_2026-10.md. The quick search keeps sending the question
as typed; interpretation only fills the advanced form for review, and the history now
carries the executed strategy so it can be reused.
"""

from __future__ import annotations

import http.client
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

import pytest

from tools.pilot_closeout_fixture import pilot_server

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "apps" / "nutev-web"
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

from query_compiler import compile_query_plan  # noqa: E402
from question_interpreter import interpret_question  # noqa: E402
from request_boundary import PUBLIC_API  # noqa: E402
import search_adapter  # noqa: E402

QUESTION = "A dieta mediterrânea melhora o controle glicêmico no diabetes tipo 2 desde 2015?"


def read(name: str) -> str:
    return (WEB_ROOT / name).read_text(encoding="utf-8")


def test_interpretation_fills_a_valid_advanced_strategy_without_executing() -> None:
    plan = interpret_question(QUESTION, current_year=2026)
    assert plan["executed"] is False and plan["plan_mode"] == "planned"
    assert plan["year_from"] == 2015
    strategy = plan["strategy"]
    assert strategy["framework"] == "PICO"
    labels = [concept["label"] for concept in strategy["concepts"]]
    assert labels == ["Type 2 diabetes", "Mediterranean diet", "Glycaemic control"]
    assert all(term.startswith("free:") for concept in strategy["concepts"] for term in concept["terms"])
    # The hosted compiler accepts it as an ordinary advanced strategy.
    compiled = compile_query_plan(QUESTION, ["pubmed", "europepmc"], strategy)
    assert compiled["mode"] == "structured_review"
    assert compiled["controlled_vocabulary_terms"] == 0  # no MeSH/DeCS invented


def test_boolean_strings_and_noise_are_not_interpreted() -> None:
    manual = interpret_question('("mediterranean diet"[tiab]) AND diabetes', current_year=2026)
    assert manual["plan_mode"] == "manual" and manual["strategy"] is None
    noise = interpret_question("a b c", current_year=2026)
    assert noise["strategy"] is None and "nothing_recognised" in noise["warnings"]
    with pytest.raises(ValueError):
        interpret_question("   ")


def test_interpreter_is_offline_and_stateless() -> None:
    source = read("question_interpreter.py")
    for forbidden in ("requests", "urllib.request", "open(", "_persist", "register_search_result"):
        assert forbidden not in source, forbidden


def test_plan_route_is_public_like_compile_and_wired() -> None:
    assert "/api/query/plan" in PUBLIC_API and "/api/query/compile" in PUBLIC_API
    assert 'path == "/api/query/plan"' in read("server.py")
    app = read("app.js")
    assert "/api/query/plan" in app and "interpretQuestionBtn" in app
    assert "window.NutEVStrategyForm" in app
    html = read("search.html")
    assert 'id="interpretQuestionBtn"' in html and "Nada é executado antes de você conferir os blocos" in html


def test_anonymous_plan_request_on_the_real_pilot_server() -> None:
    with pilot_server() as (base, _data, _extra):
        addr = urlsplit(base)
        conn = http.client.HTTPConnection(addr.hostname, addr.port, timeout=10)
        conn.request("POST", "/api/query/plan", json.dumps({"query": QUESTION}), {"Content-Type": "application/json"})
        res = conn.getresponse()
        body = json.loads(res.read())
        conn.close()
    assert res.status == 200
    assert body["strategy"]["framework"] == "PICO" and body["executed"] is False


def test_history_strategy_is_form_ready_for_each_mode() -> None:
    structured = compile_query_plan(
        "q",
        ["pubmed"],
        {"framework": "PCC", "concepts": [{"label": "Population", "terms": ["free:adults", "mesh:Obesity"]}]},
    )
    assert search_adapter._history_strategy(structured) == {
        "mode": "advanced",
        "framework": "PCC",
        "concepts": [{"label": "Population", "terms": ["free:adults", "mesh:Obesity"]}],
    }
    exact = compile_query_plan(
        "q",
        ["pubmed"],
        {"mode": "exact", "strategy_id": "s1", "strategy_version": "v1", "run_class": "DEVELOPMENT",
         "provider_queries": {"pubmed": '"diet"[tiab]'}},
    )
    assert search_adapter._history_strategy(exact) == {
        "mode": "exact",
        "strategy_id": "s1",
        "strategy_version": "v1",
        "provider_queries": {"pubmed": '"diet"[tiab]'},
    }
    assert search_adapter._history_strategy(compile_query_plan("q", ["pubmed"])) == {"mode": "quick"}
    assert search_adapter._history_strategy(None) == {"mode": "quick"}


def test_history_restores_strategy_but_never_runs_it() -> None:
    history = read("search-history-ui.js")
    assert "window.NutEVStrategyForm?.load" in history
    assert "Usar pergunta e estratégia em nova busca" in history
    assert "runSearch" not in history and "#searchBtn" not in history
