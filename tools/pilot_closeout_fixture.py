"""Temporary, offline fixture for testing the real pilot HTTP server.

Not a runtime provisioning endpoint. No production path is accepted by the CLI.
"""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from argon2 import PasswordHasher
from nutev.tenancy import (
    SQLiteAuthProvider, WorkspaceProjectService, SQLiteWorkspaceProjectStore,
    Principal, GlobalRole, new_opaque_id, ApplicationService, SQLiteApplicationStore,
    GENERIC_EVIDENCE_PROJECT,
)
from tools.multitenant_death_test import _registry_fixture

ROOT = Path(__file__).resolve().parents[1]


def seed(root: Path) -> dict:
    database = root / 'platform.sqlite3'
    auth = SQLiteAuthProvider(database, password_hasher=PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1))
    access = WorkspaceProjectService(SQLiteWorkspaceProjectStore(database))
    data = {'database': str(database), 'registry': str(root/'registry.sqlite'), 'exports': str(root/'exports'), 'users': {}}
    for label in ('a','b','admin','orphan','onboarding'):
        password = f'fixture-only {label} long password 456'
        user = auth.provision_user(email=f'{label}@example.invalid', display_name=f'Fixture {label}', password=password,
                                   global_roles={GlobalRole.PLATFORM_ADMIN} if label=='admin' else set())
        info = {'user_id':user.id, 'email':f'{label}@example.invalid','password':password}
        if label not in ('admin','orphan'):
            ws = access.provision_workspace(owner_user_id=user.id,name=f'Workspace {label}',slug=f'workspace-{label}')
            principal=Principal(user_id=user.id,global_roles=frozenset(),workspace_memberships=tuple(access.memberships_for_user(user.id)),session_id=new_opaque_id('session'))
            projects=[]
            count = 2 if label=='a' else 1
            for index in range(count):
                project=access.create_project(principal,workspace_id=ws.id,name=f'Project {label}{index}',slug=f'project-{label}{index}')
                if label != 'onboarding':
                    ApplicationService(SQLiteApplicationStore(database),access).configure(principal,workspace_id=ws.id,project_id=project.id,template_id=GENERIC_EVIDENCE_PROJECT)
                projects.append(project.id)
            info.update(workspace_id=ws.id,projects=projects)
        data['users'][label]=info
    data['article_id']=_registry_fixture(root/'registry.sqlite')
    return data


@contextmanager
def pilot_server():
    """Always owns and deletes a fresh synthetic tree; no external root argument."""
    with tempfile.TemporaryDirectory(prefix='nutev-pilot-closeout-') as temp:
        root=Path(temp)
        data=seed(root)
        with socket.socket() as s:
            s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
        env={**os.environ,'PYTHONPATH':os.pathsep.join([str(ROOT/'src'),str(ROOT)]),
             'NUTEV_AUTH_MODE':'pilot','NUTEV_AUTH_DB':data['database'],
             'NUTEV_REGISTRY_DB':data['registry'],'NUTEV_EXPORT_ROOT':data['exports'],
             'NUTEV_ENVIRONMENT':'test','NUTEV_DISABLE_NETWORK':'1','NUTEV_SEARCH_FULLTEXT_LIMIT':'0',
             'NUTEV_BUILD_COMMIT':'fixture-only-not-production'}
        script=f'''import sys\nfrom pathlib import Path\nsys.path.insert(0,{str(ROOT/'apps/nutev-web')!r})\nimport search_adapter, progress_search\nroot=Path({str(root)!r})\nsearch_adapter._output_root=lambda value=None: root\nprogress_search._output_root=lambda value=None: root\nfrom secure_server import main\nsys.argv=['secure_server','--host','127.0.0.1','--port',{str(port)!r}]\nraise SystemExit(main())\n'''
        log=(root/'server.log').open('w')
        process=subprocess.Popen([sys.executable,'-c',script],cwd=ROOT,env=env,stdout=log,stderr=log)
        base=f'http://127.0.0.1:{port}'
        try:
            for _ in range(80):
                try:
                    with urlopen(base+'/api/health',timeout=1) as response:
                        if response.status==200:break
                except OSError:time.sleep(.1)
            else:raise RuntimeError((root/'server.log').read_text())
            yield base,data,root
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            log.close()
