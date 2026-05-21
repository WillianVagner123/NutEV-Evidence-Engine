from pathlib import Path

import pytest
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from nutev.api.server import create_app
from nutev.demo.demo_data import generate_demo_data


def test_platform_endpoints_with_demo_data(tmp_path: Path):
    generate_demo_data(tmp_path)
    app = create_app(tmp_path)
    client = TestClient(app)

    assert client.get('/').status_code == 200
    assert client.get('/docs').status_code == 200
    assert client.get('/api/health').status_code == 200
    assert client.get('/api/run-summary').status_code == 200
    assert client.get('/api/evidence?limit=2').status_code == 200
    assert client.get('/api/claims').status_code == 200
    assert client.get('/api/recommendations').status_code == 200
    assert client.get('/api/human-review-queue').status_code == 200
    assert client.get('/api/human-review-decisions').status_code == 200
    assert client.get('/api/artifacts').status_code == 200
    assert client.get('/api/methods').status_code == 200


def test_platform_post_human_review_decision(tmp_path: Path):
    generate_demo_data(tmp_path)
    app = create_app(tmp_path)
    client = TestClient(app)
    payload = {
        'item_type': 'claim',
        'item_id': 'c1',
        'reviewer_name': 'R1',
        'reviewer_role': 'reviewer_1',
        'reviewer_decision': 'approve',
        'reviewer_notes': 'ok',
        'final_decision': 'pending',
    }
    before = client.get('/api/human-review-decisions').json().get('total', 0)
    r = client.post('/api/human-review-decisions', json=payload)
    assert r.status_code == 200
    assert r.json().get('item_id') == 'c1'
    after = client.get('/api/human-review-decisions').json().get('total', 0)
    assert after == before + 1

    rec_before = client.get('/api/recommendations').json()['items']
    client.post('/api/human-review-decisions', json=payload)
    rec_after = client.get('/api/recommendations').json()['items']
    assert rec_before == rec_after


def test_platform_missing_file_returns_controlled_response(tmp_path: Path):
    generate_demo_data(tmp_path)
    (tmp_path / '07_logs' / 'run_summary.json').unlink()
    app = create_app(tmp_path)
    client = TestClient(app)
    js = client.get('/api/run-summary').json()
    assert js.get('available') is False
