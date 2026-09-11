from pathlib import Path
import json
import sqlite3

from tools.audit_doctorate_runtime import A1,A2,audit


def seed(path: Path):
    with sqlite3.connect(path) as con:
        con.executescript('''
        CREATE TABLE platform_workspaces(id TEXT PRIMARY KEY,name TEXT,slug TEXT,owner_user_id TEXT,created_at TEXT,status TEXT);
        CREATE TABLE platform_projects(id TEXT PRIMARY KEY,workspace_id TEXT,name TEXT,slug TEXT,description TEXT,project_type TEXT,status TEXT,created_by TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE platform_research_applications(id TEXT PRIMARY KEY,project_id TEXT,application_type TEXT,template_id TEXT,template_version TEXT,config_version TEXT,configuration_json TEXT,status TEXT,created_by TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE article2_integrative_workflows(workflow_id TEXT PRIMARY KEY,workspace_id TEXT,project_id TEXT,application_id TEXT,config_version TEXT,current_phase TEXT,workflow_status TEXT,legacy_binding_state TEXT,legacy_binding_fingerprint TEXT,created_at TEXT,updated_at TEXT);
        ''')
        con.execute("INSERT INTO platform_workspaces VALUES('workspace_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','W','w','user_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','2026-01-01','active')")
        for suffix,assembly,kind in [('1',A1,'SCOPING_REVIEW'),('2',A2,'INTEGRATIVE_REVIEW')]:
            project=f'project_{suffix*32}';app=f'application_{suffix*32}'
            con.execute('INSERT INTO platform_projects VALUES(?,?,?,?,?,?,?,?,?,?)',(project,'workspace_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','P','p'+suffix,'',kind,'active','user_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','2026-01-01','2026-01-01'))
            con.execute('INSERT INTO platform_research_applications VALUES(?,?,?,?,?,?,?,?,?,?,?)',(app,project,kind,kind,'1.0','1',json.dumps({'assembly_id':assembly}),'active','user_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','2026-01-01','2026-01-01'))
        con.execute("INSERT INTO article2_integrative_workflows VALUES('i2w_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','workspace_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','project_22222222222222222222222222222222','application_22222222222222222222222222222222','a2-integrative-v1','LEGACY_BINDING','BLOCKED','REQUIRED_UNMATERIALIZED',NULL,'2026-01-01','2026-01-01')")


def test_read_only_doctorate_audit_reports_without_binding_or_raw_ids(tmp_path,monkeypatch):
    database=tmp_path/'auth.sqlite3';seed(database)
    root=tmp_path/'project_output_reference';(root/'agent_context/article1').mkdir(parents=True);(root/'agent_context/article1/CONTEXT_MANIFEST.json').write_text('{}')
    monkeypatch.setenv('NUTEV_A1_WORKSPACE_ID','workspace_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    monkeypatch.setenv('NUTEV_A1_PROJECT_ID','project_11111111111111111111111111111111')
    report=audit(database,root)
    assert report['status']=='PASS' and report['read_only'] is True
    assert report['article1']['application_count']==1 and report['article1']['owner_pin_state']=='OWNER_PINS_MATCH'
    assert report['article2']['workflow_count']==1 and report['article2']['historical_binding_activated'] is False
    assert report['article2']['workflows'][0]['legacy_binding_state']=='REQUIRED_UNMATERIALIZED'
    text=json.dumps(report)
    assert 'workspace_aaaaaaaa' not in text and 'project_111111' not in text and 'application_222222' not in text


def test_missing_a1_pins_are_explicit_not_inferred(tmp_path,monkeypatch):
    database=tmp_path/'auth.sqlite3';seed(database)
    root=tmp_path/'project_output_reference';root.mkdir()
    monkeypatch.delenv('NUTEV_A1_WORKSPACE_ID',raising=False);monkeypatch.delenv('NUTEV_A1_PROJECT_ID',raising=False)
    report=audit(database,root)
    assert report['article1']['owner_pin_state']=='OWNER_PINS_MISSING'
    assert report['scientific_state_modified'] is False and report['legacy_binding_performed'] is False
