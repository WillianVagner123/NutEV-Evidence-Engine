"""First-login home contract for provisioned accounts.

A user with exactly one authorized workspace and no selected context must land on
that workspace before project listing; otherwise the home page falsely renders
"Nenhum projeto disponível" even when projects exist.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "apps" / "nutev-web" / "home-dashboard.js").read_text(encoding="utf-8")


def test_home_handles_unselected_workspace_before_listing_projects() -> None:
    assert "if(!context.current?.workspace_id){" in SCRIPT
    assert SCRIPT.index("if(!context.current?.workspace_id){") < SCRIPT.index(
        "if(!context.current?.project_id){renderProjectChooser(me,context);return}"
    )


def test_single_workspace_is_opened_through_server_side_selection() -> None:
    assert "await selectWorkspace(workspaces[0].id)" in SCRIPT
    assert "'/api/context/select'" in SCRIPT
    assert "localStorage" not in SCRIPT
    assert "sessionStorage" not in SCRIPT


def test_no_workspace_and_multiple_workspaces_have_explicit_states() -> None:
    assert "function renderNoWorkspace(me)" in SCRIPT
    assert "Acesso ainda não provisionado" in SCRIPT
    assert "function renderWorkspaceChooser(me,context)" in SCRIPT
    assert "data-open-workspace" in SCRIPT
