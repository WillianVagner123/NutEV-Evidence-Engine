from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "materialize_predeploy_e2e_context.py"


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

    assert materialize in workflow
    assert workflow.index(materialize) < workflow.index(server) < workflow.index(browser)
