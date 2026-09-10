from __future__ import annotations
import http.client
import json
from pathlib import Path
import sqlite3
import sys
import time
from urllib.parse import urlsplit
import pytest
from tools.pilot_closeout_fixture import pilot_server

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'apps/nutev-web'))
from request_boundary import canonical_request_path, pilot_route_kind, same_origin_write


@pytest.fixture(scope='module')
def live():
    with pilot_server() as fixture:yield fixture


def call(base,path,method='GET',body=None,cookie='',headers=None):
    addr=urlsplit(base);conn=http.client.HTTPConnection(addr.hostname,addr.port,timeout=10)
    hs={'Cookie':cookie,**(headers or {})}
    if body is not None:hs.setdefault('Content-Type','application/json')
    conn.request(method,path,None if body is None else json.dumps(body),hs)
    res=conn.getresponse();raw=res.read();out=(res.status,raw,dict(res.getheaders()));conn.close();return out


def login(base,user):
    status,raw,headers=call(base,'/api/auth/login','POST',{'email':user['email'],'password':user['password']})
    assert status==200,raw
    return headers['Set-Cookie'].split(';')[0]


def select(base,user,cookie,index=0):
    return call(base,'/api/context/select','POST',{'workspace_id':user['workspace_id'],'project_id':user['projects'][index]},cookie)


@pytest.mark.parametrize('path',[
    '/api/radar','/api/validation/readiness','/api/validation/round','/api/validation/gold',
    '/api/synthesis/governance','/api/agent-context/article1/status','/secure_server.py',
    '/.env','/agent-context/','/server.py','/api/articles',
])
def test_legacy_science_and_source_denied_without_session(live,path):
    assert call(live[0],path)[0]==401


@pytest.mark.parametrize('path',[
    '/foo/../agent-context/article1/SEARCH_STATE.json',
    '/%61gent-context/article1/%2e%2e/secret',
    '/api%2flibrary','/%2561gent-context/article1/SEARCH_STATE.json',
    '/api/./library','/api//library','/api/\\library','/%00foo','/%ZZfoo',
])
def test_ambiguous_paths_fail_closed(live,path):
    assert call(live[0],path)[0]==400


def test_head_does_not_bypass_private_context(live):
    assert call(live[0],'/agent-context/article1/SEARCH_STATE.json','HEAD')[0]==401
    assert call(live[0],'/api/library','HEAD')[0]==405


def test_cross_origin_and_form_login_denied(live):
    base,data,_=live;u=data['users']['a']
    for headers in [{'Origin':'https://evil.example'}, {'Origin':'null'}, {'Sec-Fetch-Site':'cross-site'}, {'Content-Type':'text/plain'}]:
        assert call(base,'/api/auth/login','POST',{'email':u['email'],'password':u['password']},headers=headers)[0]==403


def test_real_tenant_library_export_search_and_stale_write(live):
    base,data,_=live;a=data['users']['a'];b=data['users']['b'];ca=login(base,a);cb=login(base,b)
    assert select(base,a,ca)[0]==200
    assert select(base,b,cb)[0]==200
    assert call(base,'/api/context/select','POST',{'workspace_id':b['workspace_id'],'project_id':b['projects'][0]},ca)[0]==404
    payload={'article_id':data['article_id'],'scope':'project','state':'not_screened','tags':[],'notes':'PRIVATE_A_FIXTURE'}
    status,raw,_=call(base,'/api/library/placements','POST',payload,ca);assert status in {200,201},raw
    status,raw,headers=call(base,'/api/library?scope=project',cookie=ca);assert status==200 and b'PRIVATE_A_FIXTURE' in raw
    assert 'no-store' in headers['Cache-Control']
    entry=json.loads(raw)['entries'][0]['placement']['placement_id']
    assert call(base,'/api/library/placements/'+entry,cookie=cb)[0]==404
    assert call(base,'/api/library/placements/'+entry,'DELETE',cookie=cb)[0]==404
    assert b'PRIVATE_A_FIXTURE' not in call(base,'/api/library?scope=project',cookie=cb)[1]
    assert select(base,a,ca,1)[0]==200
    stale={'X-NutEV-User':a['user_id'],'X-NutEV-Workspace':a['workspace_id'],'X-NutEV-Project':a['projects'][0]}
    assert call(base,'/api/library/placements','POST',payload,ca,stale)[0]==409
    assert b'PRIVATE_A_FIXTURE' not in call(base,'/api/library?scope=project',cookie=ca)[1]
    assert select(base,a,ca)[0]==200
    payload_export={'export_kind':'fixture','artifacts':[{'name':'fixture.txt','media_type':'text/plain','content_text':'PRIVATE_EXPORT_A'}]}
    status,raw,_=call(base,'/api/exports','POST',payload_export,ca)
    # Exact payload contract is tested below, never silently count a rejected export as successful.
    assert status in {200,201},raw
    export_id=json.loads(raw)['export']['id']
    assert call(base,f'/api/exports/{export_id}/manifest',cookie=cb)[0]==404
    assert call(base,f'/api/exports/{export_id}/artifacts/fixture.txt',cookie=cb)[0]==404
    assert call(base,f'/api/exports/{export_id}/artifacts/fixture.txt',cookie=ca)[1]==b'PRIVATE_EXPORT_A'
    assert json.loads(call(base,'/api/audit',cookie=ca)[1])['chain_valid'] is True
    status,raw,_=call(base,'/api/search/jobs','POST',{'query':'fixture test evidence','providers':['pubmed'],'per_provider':1,'max_results':1},ca)
    assert status==202,raw;job_id=json.loads(raw)['job_id']
    for _ in range(50):
        status,raw,_=call(base,'/api/search/jobs/'+job_id,cookie=ca);job=json.loads(raw)
        if job['status']=='completed':break
        time.sleep(.1)
    assert job['status']=='completed',job
    assert all(p['status']=='skipped' for p in job['result']['providers'])
    assert call(base,'/api/search/jobs/'+job_id,cookie=cb)[0]==404
    assert call(base,'/api/searches/'+job['search_id'],cookie=cb)[0]==404
    assert call(base,'/api/articles',cookie=ca)[0]==404
    assert call(base,'/api/radar',cookie=ca)[0]==404
    assert call(base,'/api/auth/logout','POST',{},ca)[0]==200
    assert call(base,'/api/library?scope=project',cookie=ca)[0]==401


def test_admin_cannot_bypass_private_scope(live):
    base,data,_=live;cookie=login(base,data['users']['admin'])
    status,raw,_=call(base,'/api/library',cookie=cookie)
    assert status in {403,409} and b'PRIVATE_A_FIXTURE' not in raw


def test_expiration_and_membership_revocation(live):
    base,data,_=live;u=data['users']['b'];cookie=login(base,u);assert select(base,u,cookie)[0]==200
    with sqlite3.connect(data['database']) as con:
        con.execute("UPDATE platform_workspace_memberships SET status='removed' WHERE user_id=?",(u['user_id'],))
    assert call(base,'/api/library',cookie=cookie)[0] in {403,409}
    with sqlite3.connect(data['database']) as con:
        con.execute("UPDATE platform_auth_sessions SET expires_at='2000-01-01T00:00:00+00:00' WHERE user_id=?",(u['user_id'],))
    assert call(base,'/api/library',cookie=cookie)[0]==401


def test_boundary_allowlist_and_punctuation():
    assert canonical_request_path('/api/searches/web_1%2B0')=='/api/searches/web_1+0'
    assert pilot_route_kind('/api/article1/d132/review')=='guest_scoped'
    assert pilot_route_kind('/agent-context/article1/SEARCH_STATE.json')=='article1_context'
    assert same_origin_write({'Origin':'https://example.org','Host':'example.org','Content-Type':'application/json'},secure=True)
