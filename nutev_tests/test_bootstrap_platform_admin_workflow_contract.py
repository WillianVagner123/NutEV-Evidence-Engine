from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "bootstrap-platform-admin.yml"


def test_bootstrap_workflow_verifies_expected_identity_and_role_without_credentials() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Verify bootstrap identity and PLATFORM_ADMIN role" in workflow
    assert "bootstrap_identity_present=" in workflow
    assert "bootstrap_identity_active=" in workflow
    assert "bootstrap_platform_admin=" in workflow
    assert "SELECT status, global_roles_json FROM platform_auth_users" in workflow
    assert "WHERE email = ? COLLATE NOCASE LIMIT 1" in workflow
    assert "BOOTSTRAP_ADMIN_EMAIL" in workflow
    assert "password_hash" not in workflow
    assert "session_token" not in workflow
    assert "Bootstrap administrator identity/role verification failed" in workflow
    assert "without mutating credentials, memberships, projects, or scientific state" in workflow
