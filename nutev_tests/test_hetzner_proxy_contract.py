from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_proxy_inventory_is_read_only_and_reports_mode():
    text = (ROOT / 'tools/remote_proxy_inventory.sh').read_text()
    assert 'NUTEV_PROXY_MODE=' in text
    assert 'PORT80_LISTENER=' in text and 'PORT443_LISTENER=' in text
    assert 'docker ps --format' in text
    assert 'systemctl is-active' in text
    for forbidden in ('docker stop', 'docker rm', 'systemctl stop', 'systemctl restart', 'kill ', 'pkill'):
        assert forbidden not in text
    result = subprocess.run(['bash', '-n', 'tools/remote_proxy_inventory.sh'], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_deploy_preserves_unknown_proxy_and_selects_services():
    text = (ROOT / '.github/workflows/deploy-hetzner.yml').read_text()
    assert 'Inspect 80/443 ownership before any service mutation' in text
    assert 'PROXY_MODE: ${{ steps.proxy.outputs.mode }}' in text
    assert 'DEPLOY_SERVICES=(nutev)' in text
    assert 'DEPLOY_SERVICES+=(caddy)' in text
    assert 'RESTORE_SERVICES=(nutev)' in text
    assert 'RESTORE_SERVICES+=(caddy)' in text
    assert 'External proxy owns 80/443 but the current NutEV public route is not reachable' in text
    assert 'No listener on 80/443; NutEV will manage its own Caddy.' in text
    assert 'Existing listener detected; NutEV will not stop or replace it.' in text


def test_external_proxy_mode_never_requires_starting_caddy():
    text = (ROOT / '.github/workflows/deploy-hetzner.yml').read_text()
    old = 'up -d --no-build nutev caddy'
    assert old not in text
    assert '"${DEPLOY_SERVICES[@]}"' in text
    assert '"${RESTORE_SERVICES[@]}"' in text
