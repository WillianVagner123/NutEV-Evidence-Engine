from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "hetzner-readiness.yml"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readiness_is_manual_main_only_and_uses_production_environment() -> None:
    workflow = " ".join(read(WORKFLOW).split())

    assert "workflow_dispatch:" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "environment: HETZNER" in workflow
    assert "secrets.HETZNER_SSH_KEY" in workflow
    assert "vars.HETZNER_HOST" in workflow
    assert "vars.HETZNER_USER" in workflow
    assert "vars.HETZNER_APP_DIR" in workflow


def test_readiness_validates_same_supported_key_representations_as_deploy() -> None:
    workflow = read(WORKFLOW)

    assert 'raw.replace("\\r\\n", "\\n").replace("\\r", "\\n")' in workflow
    assert 'raw.replace("\\\\n", "\\n")' in workflow
    assert "base64.b64decode" in workflow
    assert "ssh-keygen -y -P '' -f ~/.ssh/id_ed25519" in workflow
    assert "-o BatchMode=yes" in workflow
    assert "-o IdentitiesOnly=yes" in workflow
    assert "-o ConnectTimeout=15" in workflow


def test_readiness_checks_remote_prerequisites_without_deploying() -> None:
    workflow = read(WORKFLOW)

    required = (
        "test -d .git",
        "test -f deploy/hetzner/.env",
        "test -f deploy/hetzner/compose.yaml",
        "test -f deploy/hetzner/Dockerfile",
        "docker info",
        "docker compose version",
        "git rev-parse HEAD",
        "df -Pk",
        "http://127.0.0.1:8765/api/health",
        "http://127.0.0.1:8765/api/version",
    )
    for marker in required:
        assert marker in workflow

    forbidden = (
        "git reset --hard",
        "git checkout -f",
        "docker build",
        "docker run",
        "docker rm",
        "docker image prune",
        " compose up ",
        " compose down ",
        " down -v",
    )
    for marker in forbidden:
        assert marker not in workflow
