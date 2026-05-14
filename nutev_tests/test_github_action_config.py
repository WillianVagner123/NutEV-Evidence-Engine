from pathlib import Path

def test_workflow_exists():
    assert Path('.github/workflows/nutev-global-watch.yml').exists()
