from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "configure-production-smtp.yml"


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_smtp_workflow_is_manual_main_only_and_hetzner_gated() -> None:
    workflow = _workflow()
    triggers = workflow[True] if True in workflow else workflow["on"]

    assert set(triggers) == {"workflow_dispatch"}
    job = workflow["jobs"]["smtp"]
    assert job["if"].strip() == "${{ github.ref == 'refs/heads/main' }}"
    assert job["environment"] == "HETZNER"
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] is False


def test_smtp_password_is_never_a_workflow_input_or_plaintext_literal() -> None:
    workflow = _workflow()
    triggers = workflow[True] if True in workflow else workflow["on"]
    inputs = triggers["workflow_dispatch"]["inputs"]
    body = WORKFLOW.read_text(encoding="utf-8")

    assert "password" not in {str(name).casefold() for name in inputs}
    assert "secrets.NUTEV_SMTP_PASSWORD" in body
    assert "secrets.HETZNER_SSH_KEY" in body
    assert "SMTP_PASSWORD: ${{ secrets.NUTEV_SMTP_PASSWORD }}" in body
    assert 'echo "$SMTP_PASSWORD"' not in body
    assert "print(os.environ.get(\"SMTP_PASSWORD\"" not in body
    assert "upload-artifact" not in body


def test_inspect_is_read_only_and_apply_is_explicit() -> None:
    workflow = _workflow()
    steps = workflow["jobs"]["smtp"]["steps"]
    apply = next(step for step in steps if step.get("name") == "Apply SMTP configuration with rollback")

    assert apply["if"].strip() == "${{ inputs.mode == 'apply' }}"

    inspect_script = next(
        step["run"] for step in steps if step.get("name") == "Inspect current production SMTP state"
    )
    assert "SMTP_CONNECTIVITY_READY=" in inspect_script
    assert "PASSWORD_RESET_DELIVERY_READY=" in inspect_script
    assert "docker compose" in inspect_script
    assert " up -d " not in inspect_script
    assert "SQLitePasswordResetStore" not in inspect_script


def test_apply_is_atomic_rolls_back_and_preserves_production_sha() -> None:
    body = WORKFLOW.read_text(encoding="utf-8")

    assert "BACKUP=\"$(mktemp deploy/hetzner/.env.smtp-backup." in body
    assert "SMTP configuration failed; restoring the previous production environment." in body
    assert 'cp "$BACKUP" deploy/hetzner/.env' in body
    assert "up -d --no-build nutev" in body
    assert '[[ "$NEW_COMMIT" = "$OLD_COMMIT" ]]' in body
    assert "PRODUCTION_SHA_PRESERVED=" in body
    assert 'rm -f "$STAGE" "$BACKUP"' in body


def test_apply_requires_live_smtp_probe_before_marking_ready() -> None:
    body = WORKFLOW.read_text(encoding="utf-8")

    assert "smtplib.SMTP(host, port, timeout=15)" in body
    assert "client.starttls" in body
    assert "client.login(username, password)" in body
    assert "client.noop()" in body
    assert "SMTP_CONNECTIVITY_READY=true" in body
    assert "PASSWORD_RESET_DELIVERY_READY=true" in body
    assert 'grep -Fxq "PUBLIC_ORIGIN_EFFECTIVE=$PUBLIC_URL"' in body


def test_optional_bootstrap_reset_uses_canonical_store_without_logging_token() -> None:
    body = WORKFLOW.read_text(encoding="utf-8")

    assert "SQLitePasswordResetStore(database).issue(email)" in body
    assert "send_password_reset_email(" in body
    assert "BOOTSTRAP_PASSWORD_RESET_DELIVERY=sent" in body
    assert "print(ticket.token)" not in body
    assert "echo \"$ticket.token\"" not in body
    assert "password_updated" not in body


def test_smtp_workflow_never_touches_scientific_state_or_project_permissions() -> None:
    body = WORKFLOW.read_text(encoding="utf-8")

    forbidden = (
        "Article 1",
        "D-132",
        "PRESS",
        "Jev",
        "grant_workspace_membership",
        "grant_platform_admin",
        "NUTEV_A1_WORKSPACE_ID",
        "NUTEV_A1_PROJECT_ID",
        "formal search",
        "ranking",
    )
    for token in forbidden:
        assert token not in body
