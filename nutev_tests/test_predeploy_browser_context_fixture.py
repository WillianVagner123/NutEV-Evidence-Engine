from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "materialize_predeploy_e2e_context.py"
MATRIX = ROOT / "tools" / "run_predeploy_search_ui_execution_matrix.py"


def test_browser_context_fixture_is_explicitly_test_only_and_rank_blind() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "PRE-DEPLOY UI FIXTURE ONLY" in source
    assert '"test_fixture_only": True' in source
    assert '"rank_blind": True' in source
    assert '"full_text_included": False' in source
    assert '"eligibility_decisions_included": False' in source
    assert '"prisma_events_included": False' in source

    for forbidden in (
        "reference_rank",
        "reference_score",
        "reference_tier",
        "machine_relevance_score",
        "machine_relevance_band",
    ):
        assert forbidden not in source


def test_browser_workflow_materializes_fixture_before_server_start() -> None:
    workflow = (ROOT / ".github" / "workflows" / "predeploy-browser-e2e.yml").read_text(
        encoding="utf-8"
    )

    materialize = "python tools/materialize_predeploy_e2e_context.py"
    server = "python apps/nutev-web/secure_server.py"
    browser = "python tools/run_predeploy_browser_e2e.py"
    matrix = "python tools/run_predeploy_search_ui_execution_matrix.py"

    assert materialize in workflow
    assert browser in workflow
    assert matrix in workflow
    assert workflow.index(materialize) < workflow.index(server) < workflow.index(browser)
    assert workflow.index(browser) < workflow.index(matrix)


def test_browser_search_matrix_executes_all_ten_modes_in_one_session() -> None:
    source = MATRIX.read_text(encoding="utf-8")

    assert 'for framework in ("PCC", "PICO", "PECO")' in source
    assert "quick_runs == 2" in source
    assert "structured_runs == 6" in source
    assert "exact_runs == 2" in source
    assert "page.expect_response" in source
    assert 'response.request.method == "POST"' in source
    assert "completed job has no persisted result" in source
    assert "interactive_bounded" in source
    assert "global_exhaustive" in source
    assert "structured_review_bounded" in source
    assert "structured_review_global_exhaustive" in source
    assert "exact_review_bounded" in source
    assert "exact_review_global_exhaustive" in source
    assert "Exact bounded rewrote the literal PubMed query" in source
    assert "Exact global rewrote the literal PubMed query" in source
    assert "history_count >= 10" in source
    assert "provider gaps were not surfaced" in source
