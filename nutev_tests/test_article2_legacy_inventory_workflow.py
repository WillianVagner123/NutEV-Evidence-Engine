from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "article2-legacy-runtime-inventory.yml"
TOOL = ROOT / "tools" / "inventory_article2_legacy_runtime.py"


def test_article2_inventory_workflow_is_manual_main_only_and_fail_closed() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "environment: HETZNER" in text
    assert "ARTICLE2_LEGACY_RUNTIME_INVENTORY_PASS" in text
    assert "UNKNOWN_UNTIL_REVIEW" in text
    assert "NOT_CREATED_REVIEW_REQUIRED" in text
    assert "legacy_binding_performed" in text
    assert "ownership_inferred_from_names" in text
    assert "raw_path_exposed" in text
    assert "query_text_exposed" in text
    assert "search_id_exposed" in text
    assert "register_legacy_binding" not in text
    assert "/legacy-binding" not in text
    assert "/activate" not in text
    assert "NUTEV_ARTICLE2_ENABLED" not in text


def test_article2_inventory_scans_host_and_current_container_without_exposing_raw_paths() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '--root "$APP_DIR" --root "$APP_PARENT"' in text
    assert "exec -T nutev python - --root /app --max-depth 1 --json" in text
    assert "article2-legacy-runtime-inventory.json" in text
    assert "actions/upload-artifact@" in text


def test_inventory_tool_has_no_binding_or_scientific_mutation_surface() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert "LegacyBindingEvidence" in text
    assert '"legacy_binding_performed": False' in text
    assert '"scientific_state_modified": False' in text
    assert '"search_executed": False' in text
    assert '"ownership": "UNKNOWN_UNTIL_REVIEW"' in text
    assert "register_legacy_binding" not in text
    assert "ARTICLE2_PRIVATE" not in text
