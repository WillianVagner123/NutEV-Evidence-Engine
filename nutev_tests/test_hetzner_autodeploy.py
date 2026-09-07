from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy" / "hetzner"
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-hetzner.yml"
SECURE_SERVER = ROOT / "apps" / "nutev-web" / "secure_server.py"


def test_hetzner_compose_preserves_data_and_keeps_backend_private() -> None:
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    assert '127.0.0.1:8765:8765' in compose
    assert '"8765:8765"' not in compose.replace('127.0.0.1:8765:8765', '')
    assert 'nutev_output:/app/project_output_reference' in compose
    assert 'no-new-privileges:true' in compose
    assert '${NUTEV_IMAGE:-nutev-local:latest}' in compose


def test_autodeploy_is_guarded_by_ci_and_explicit_enable_flag() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'workflows: ["ci"]' in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert "vars.HETZNER_AUTODEPLOY == 'true'" in workflow
    assert 'environment: HETZNER' in workflow
    assert 'HETZNER_HOST: ${{ vars.HETZNER_HOST }}' in workflow
    assert 'HETZNER_USER: ${{ vars.HETZNER_USER }}' in workflow
    assert 'HETZNER_PORT: ${{ vars.HETZNER_PORT }}' in workflow
    assert 'HETZNER_APP_DIR: ${{ vars.HETZNER_APP_DIR }}' in workflow
    assert 'HETZNER_SSH_KEY: ${{ secrets.HETZNER_SSH_KEY }}' in workflow


def test_autodeploy_preflights_and_rolls_back_on_health_failure() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert '127.0.0.1:18765:8765' in workflow
    assert 'http://127.0.0.1:18765/api/health' in workflow
    assert 'http://127.0.0.1:8765/api/health' in workflow
    assert 'docker tag "$OLD_IMAGE_ID" nutev:rollback' in workflow
    assert 'NUTEV_IMAGE=nutev:rollback' in workflow
    assert 'docker compose --env-file deploy/hetzner/.env' in workflow


def test_deploy_files_do_not_embed_secrets() -> None:
    env_example = (DEPLOY / ".env.example").read_text(encoding="utf-8")
    caddy = (DEPLOY / "Caddyfile").read_text(encoding="utf-8")
    assert 'REPLACE_WITH_CADDY_PASSWORD_HASH' in env_example
    assert '{$NUTEV_BASIC_AUTH_HASH}' in caddy
    assert 'BEGIN OPENSSH PRIVATE KEY' not in WORKFLOW.read_text(encoding="utf-8")


def test_build_identity_is_image_owned_not_persistent_env_owned() -> None:
    env_example = (DEPLOY / ".env.example").read_text(encoding="utf-8")
    dockerfile = (DEPLOY / "Dockerfile").read_text(encoding="utf-8")
    server = SECURE_SERVER.read_text(encoding="utf-8")

    for key in (
        "NUTEV_BUILD_COMMIT=",
        "NUTEV_BUILD_BRANCH=",
        "NUTEV_BUILD_TIME=",
        "NUTEV_VERSION=",
    ):
        assert key not in env_example

    assert '> /app/apps/nutev-web/build-info.json' in dockerfile
    assert '"build_commit":"%s"' in dockerfile
    assert '"build_branch":"%s"' in dockerfile
    assert '"build_time":"%s"' in dockerfile
    assert 'CMD ["sh", "-lc", "printf' not in dockerfile

    assert 'info.get("version") or os.environ.get("NUTEV_VERSION")' in server
    assert 'info.get("build_commit") or os.environ.get("NUTEV_BUILD_COMMIT")' in server
    assert 'info.get("build_branch") or os.environ.get("NUTEV_BUILD_BRANCH")' in server
    assert 'info.get("build_time") or os.environ.get("NUTEV_BUILD_TIME")' in server
