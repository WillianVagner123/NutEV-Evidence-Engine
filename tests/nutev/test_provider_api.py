from pathlib import Path
import pytest

fastapi = pytest.importorskip('fastapi')
from fastapi.testclient import TestClient

from nutev.api.server import create_app
from nutev.demo.demo_data import generate_demo_data


def test_provider_endpoints_mask_and_save(tmp_path: Path):
    generate_demo_data(tmp_path)
    app = create_app(tmp_path)
    c = TestClient(app)

    js = c.get('/api/providers').json()
    assert js['available'] is True

    c.post('/api/provider-settings', json={'providers': {'openai': {'enabled': True, 'mode': 'assistive', 'env_var': 'OPENAI_API_KEY', 'secret_source': 'local', 'api_key': 'secret123', 'local_only': True}}})
    got = c.get('/api/provider-settings').json()
    assert got['providers']['openai']['api_key'] != 'secret123'


def test_provider_test_statuses(tmp_path: Path):
    generate_demo_data(tmp_path)
    app = create_app(tmp_path)
    c = TestClient(app)

    c.post('/api/provider-settings', json={'providers': {'openai': {'enabled': True, 'mode': 'assistive', 'env_var': 'OPENAI_API_KEY', 'secret_source': 'env'}}})
    r = c.post('/api/provider-settings/test', json={'provider_id': 'openai'}).json()
    assert r['status'] in {'missing_key', 'ok'}

    c.post('/api/provider-settings', json={'providers': {'ollama': {'enabled': True, 'mode': 'assistive', 'base_url': 'http://127.0.0.1:65530'}}})
    ro = c.post('/api/provider-settings/test', json={'provider_id': 'ollama'}).json()
    assert ro['status'] in {'provider_unavailable', 'ok'}
