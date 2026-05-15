from pathlib import Path

def test_workflow_exists():
    assert Path('.github/workflows/nutev-global-watch.yml').exists()


def test_workflow_has_webhook_env():
    txt = Path('.github/workflows/nutev-global-watch.yml').read_text(encoding='utf-8')
    assert "NUTEV_DIGEST_WEBHOOK_URL" in txt
