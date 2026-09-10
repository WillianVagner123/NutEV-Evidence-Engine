"""Static release linkage guards; no claim of Docker/production execution."""
from pathlib import Path
import json
import yaml

ROOT=Path(__file__).resolve().parents[1]

def test_host_identity_is_pinned_before_access():
    for name in ('deploy-hetzner.yml','hetzner-readiness.yml'):
        text=(ROOT/'.github/workflows'/name).read_text()
        assert 'ssh-keyscan ' not in text
        assert 'HETZNER_KNOWN_HOSTS' in text
        assert '-o StrictHostKeyChecking=yes' in text
        data=yaml.safe_load(text)
        for job in data['jobs'].values():
            assert 'HETZNER_SSH_KEY' not in job.get('env',{})

def test_restore_proof_precedes_promotion():
    text=(ROOT/'.github/workflows/deploy-hetzner.yml').read_text()
    assert text.index('docker stop "$OLD_CONTAINER"') < text.index('tools/recovery_snapshot.py')
    assert text.index('tools/recovery_snapshot.py') < text.index('PROMOTED=1')
    assert text.index('restore-proof.json') < text.index('PROMOTED=1')
    assert 'docker ps -q --filter volume=' in text
    assert '"$OUTPUT_VOLUME:/snapshot-source:ro"' in text
    assert '--env-file "$RECOVERY_DIR/config/.env"' in text
    assert '-f "$RECOVERY_DIR/config/compose.yaml"' in text
    assert '"$RESTORED_COMMIT" = "$OLD_COMMIT"' in text

def test_pilot_image_does_not_materialize_article1():
    line=next(s for s in (ROOT/'deploy/hetzner/Dockerfile').read_text().splitlines() if s.startswith('CMD '))
    command=json.loads(line[4:])[-1]
    assert 'if [ "${NUTEV_AUTH_MODE:-legacy}" = legacy ]; then if python tools/build_article1_agent_context.py' in command
    assert command.endswith('--host 0.0.0.0 --port 8765')

def test_pilot_browser_is_required_by_release_verifier():
    from tools.check_release_prerequisites import REQUIRED
    assert any('Authenticated pilot browser closeout' in str(v) for v in REQUIRED.values())
    text=(ROOT/'.github/workflows/predeploy-browser-e2e.yml').read_text()
    assert 'python tools/run_pilot_browser_closeout.py' in text
