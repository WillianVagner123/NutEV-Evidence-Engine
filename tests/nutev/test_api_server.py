from pathlib import Path
import pytest

fastapi = pytest.importorskip('fastapi')
from fastapi.testclient import TestClient

from nutev.api.server import create_app
from nutev.demo.demo_data import generate_demo_data


def test_api_server_endpoints(tmp_path: Path):
    generate_demo_data(tmp_path)
    app = create_app(tmp_path)
    c = TestClient(app)
    assert c.get('/').status_code == 200
    assert c.get('/docs').status_code == 200
    assert c.get('/api/health').json()['status'] == 'ok'
    assert c.get('/api/run-summary').status_code == 200
    assert c.get('/api/evidence').json()['available'] is True
    assert c.get('/api/claims').json()['available'] is True
    assert c.get('/api/recommendations').json()['available'] is True
    assert c.get('/api/human-review-queue').status_code == 200
    assert c.get('/api/artifacts').json()['available'] is True


def test_api_append_only_decision_and_missing_file_safe(tmp_path: Path):
    generate_demo_data(tmp_path)
    app = create_app(tmp_path)
    c = TestClient(app)
    payload = {
        'item_type': 'claim', 'item_id': 'c1', 'reviewer_name': 'R',
        'reviewer_role': 'reviewer_1', 'reviewer_decision': 'approve',
        'reviewer_notes': 'ok', 'final_decision': 'pending'
    }
    before = c.get('/api/human-review-decisions').json()['total']
    c.post('/api/human-review-decisions', json=payload)
    after = c.get('/api/human-review-decisions').json()['total']
    assert after == before + 1

    # remove run summary to verify missing returns available=false
    (tmp_path/'07_logs'/'run_summary.json').unlink()
    js = c.get('/api/run-summary').json()
    assert js.get('available') is False
