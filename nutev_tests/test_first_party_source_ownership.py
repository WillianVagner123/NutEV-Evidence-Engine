"""Private first-party source access must not trust a writable application label."""
from pathlib import Path
from types import SimpleNamespace
import sys

WEB = Path(__file__).resolve().parents[1] / 'apps/nutev-web'
sys.path.insert(0, str(WEB))
import tenant_release_guard as guard

WORKSPACE = 'wsp_' + 'a' * 32
PROJECT = 'prj_' + 'b' * 32


def test_forged_application_name_does_not_authorize_global_a1_source(monkeypatch):
    monkeypatch.delenv('NUTEV_A1_WORKSPACE_ID', raising=False)
    monkeypatch.delenv('NUTEV_A1_PROJECT_ID', raising=False)
    monkeypatch.setattr(guard, '_project_context', lambda handler: (object(), WORKSPACE, PROJECT))
    fake = SimpleNamespace(descriptor=lambda: {'template_id': 'SCOPING_REVIEW', 'configuration': {'assembly_id': 'WILLIAN_DOCTORATE_A1'}})
    monkeypatch.setattr(guard, 'application_service', lambda: SimpleNamespace(get=lambda *a, **k: fake))
    responses = []
    handler = SimpleNamespace(_json=lambda body, status: responses.append((body, status)))
    assert guard._article1_context_allowed(handler) is False
    assert responses[-1][1] == 404


def test_server_owner_pin_is_required_for_both_dimensions(monkeypatch):
    from first_party_source_access import article1_source_owner_allowed
    monkeypatch.setenv('NUTEV_A1_WORKSPACE_ID', WORKSPACE)
    monkeypatch.setenv('NUTEV_A1_PROJECT_ID', PROJECT)
    assert article1_source_owner_allowed(WORKSPACE, PROJECT)
    assert not article1_source_owner_allowed('wsp_' + 'c' * 32, PROJECT)
    assert not article1_source_owner_allowed(WORKSPACE, 'prj_' + 'c' * 32)
    monkeypatch.setenv('NUTEV_A1_PROJECT_ID', 'Artigo 1')
    assert not article1_source_owner_allowed(WORKSPACE, 'Artigo 1')


def test_owner_endpoint_denies_before_loading_private_source(monkeypatch):
    import article1_d132_api as api
    monkeypatch.delenv('NUTEV_A1_WORKSPACE_ID', raising=False)
    monkeypatch.delenv('NUTEV_A1_PROJECT_ID', raising=False)
    monkeypatch.setattr(api, '_project_context', lambda handler: (object(), WORKSPACE, PROJECT))
    monkeypatch.setattr(api, '_applications', lambda: (_ for _ in ()).throw(AssertionError('must not read private application')))
    responses=[]
    handler=SimpleNamespace(_json=lambda body,status:responses.append((body,status)))
    assert api._article1_project_context(handler) is None
    assert responses[-1][1] == 404


def test_existing_guest_cannot_access_a_source_with_different_owner(monkeypatch):
    import article1_d132_api as api
    from nutev.review import ReviewAccessDenied
    import pytest
    monkeypatch.setenv('NUTEV_A1_WORKSPACE_ID', WORKSPACE)
    monkeypatch.setenv('NUTEV_A1_PROJECT_ID', PROJECT)
    access=SimpleNamespace(workspace_id=WORKSPACE,project_id='prj_'+'c'*32)
    monkeypatch.setattr(api,'_service',lambda:SimpleNamespace(engine=SimpleNamespace(access_for_guest=lambda token:access)))
    with pytest.raises(ReviewAccessDenied):api._require_guest_source_owner('fixture-token')
    access.project_id=PROJECT
    api._require_guest_source_owner('fixture-token')


def test_real_http_application_configuration_is_not_ownership():
    from tools.pilot_closeout_fixture import pilot_server
    import requests
    with pilot_server() as (base,data,_):
        user=data['users']['a']
        with requests.Session() as session:
            response=session.post(base+'/api/auth/login',json={'email':user['email'],'password':user['password']},timeout=5)
            assert response.status_code==200
            response=session.post(base+'/api/context/select',json={'workspace_id':user['workspace_id'],'project_id':user['projects'][0]},timeout=5)
            assert response.status_code==200
            response=session.post(base+'/api/application',json={'template_id':'SCOPING_REVIEW','configuration':{'assembly_id':'WILLIAN_DOCTORATE_A1','d132_config_version':'a1-d132-v1'}},timeout=5)
            assert response.status_code in {200,201}
            response=session.get(base+'/agent-context/article1/SEARCH_STATE.json',timeout=5)
            assert response.status_code==404
            assert response.json()['error']=='article1_context_not_found'
            response=session.post(base+'/api/article1/d132/rounds',json={},timeout=5)
            assert response.status_code==404
            assert response.json()['error']=='article1_project_not_found'
