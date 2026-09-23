from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERIGNORE = ROOT / ".dockerignore"
RUNTIME_CHECK = ROOT / "tools" / "check_predeploy_runtime_contract.py"

D132_ROOT = "evidence/article1_press/article1_press_20260906T202201Z"
D132_FILES = (
    "HUMAN_REVIEW_SAMPLE_MANIFEST.json",
    "HUMAN_REVIEW_SAMPLE_D02.csv",
    "HUMAN_REVIEW_SAMPLE_D03.csv",
    "HUMAN_REVIEW_SAMPLE_D04.csv",
    "HUMAN_REVIEW_SAMPLE_D05.csv",
)


def test_docker_context_allows_only_canonical_d132_custody_files_from_evidence_tree() -> None:
    text = DOCKERIGNORE.read_text(encoding="utf-8")

    assert "!evidence/" in text
    assert "evidence/**" in text
    assert "!evidence/article1_press/" in text
    assert "evidence/article1_press/**" in text
    assert f"!{D132_ROOT}/" in text
    assert f"{D132_ROOT}/**" in text
    for name in D132_FILES:
        assert f"!{D132_ROOT}/{name}" in text

    # Never broaden production Docker custody to the whole scientific evidence tree.
    assert "!evidence/**" not in text
    assert "!evidence/article1_press/**" not in text
    assert f"!{D132_ROOT}/**" not in text


def test_predeploy_runtime_contract_fails_closed_when_d132_source_is_not_loadable() -> None:
    text = RUNTIME_CHECK.read_text(encoding="utf-8")

    assert "load_d132_config" in text
    assert "load_d132_source" in text
    assert '"article1_d132_source_custody"' in text
    assert '"FAIL"' in text
    assert '{"D02": 25, "D03": 25, "D04": 25, "D05": 25}' in text
    assert 'd132_source.selected_record_count != 100' in text
