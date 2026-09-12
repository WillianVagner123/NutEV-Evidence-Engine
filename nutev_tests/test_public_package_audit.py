from __future__ import annotations

import io
from pathlib import Path
import tarfile
import zipfile

import pytest

from tools.audit_public_package import audit_distribution, check_name

VERSION = '1.1.0'
ROOT = f'nutev_nutmev-{VERSION}'
DOI = '10.5281/zenodo.22726717'
RELEASE_DATE = '2026-09-12'


def wheel(tmp_path, extra=None, version=VERSION):
    path = tmp_path / f'{ROOT}-py3-none-any.whl'
    with zipfile.ZipFile(path, 'w') as archive:
        for name in ('__init__.py', 'cli.py', '__version__.py'):
            archive.writestr('nutev/' + name, '# synthetic package fixture\n')
        archive.writestr(ROOT + '.dist-info/METADATA', f'Name: nutev-nutmev\nVersion: {version}\n')
        archive.writestr(ROOT + '.dist-info/licenses/LICENSE', 'MIT License - synthetic fixture')
        for name, value in (extra or {}).items():
            archive.writestr(name, value)
    return path


def test_expected_wheel_is_inventoried_without_extraction(tmp_path):
    report = audit_distribution(wheel(tmp_path), VERSION)
    assert report['status'] == 'PASS'
    assert len(report['members']) == 5
    assert len(report['sha256']) == 64


@pytest.mark.parametrize('name', [
    '../outside.py', '/absolute.py', 'nutev/../private.py', 'nutev//bad.py',
    'nutev\\bad.py', 'nutev/.env', 'nutev/key.pem', 'nutev/private_data/secret.py',
    'nutev/project_output_private/state.py', 'nutev/state.sqlite', 'nutev/state.sqlite-wal',
    'nutev/report.pdf', 'nutev/bad\n.py', 'C:/file.py',
])
def test_unsafe_or_private_path_rejected(name):
    with pytest.raises(ValueError):
        check_name(name)


@pytest.mark.parametrize('extra', [
    {'config/article1_queries.json': '{}'},
    {'nutev/plain.txt': 'not an allowlisted module'},
    {'nutev/data.py': b'SQLite format 3\x00'},
    {'nutev/data.py': b'NUTEV_PACKAGE_PRIVATE_' + b'CANARY'},
    {'nutev/data.py': b'-----BEGIN ' + b'PRIVATE KEY-----'},
])
def test_forbidden_content_and_distribution_scope_rejected(tmp_path, extra):
    with pytest.raises(ValueError):
        audit_distribution(wheel(tmp_path, extra), VERSION)


def test_metadata_version_mismatch_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        audit_distribution(wheel(tmp_path, version='1.0.0'), VERSION)


def test_duplicate_member_is_rejected(tmp_path):
    path = wheel(tmp_path)
    with zipfile.ZipFile(path, 'a') as archive:
        with pytest.warns(UserWarning):
            archive.writestr('nutev/cli.py', '# duplicate')
    with pytest.raises(ValueError):
        audit_distribution(path, VERSION)


def test_symlink_is_rejected(tmp_path):
    path = wheel(tmp_path)
    with zipfile.ZipFile(path, 'a') as archive:
        item = zipfile.ZipInfo('nutev/link.py')
        item.create_system = 3
        item.external_attr = 0o120777 << 16
        archive.writestr(item, '/etc/passwd')
    with pytest.raises(ValueError):
        audit_distribution(path, VERSION)


def test_sdist_is_audited_and_rejects_hardlinks(tmp_path):
    path = tmp_path / f'{ROOT}.tar.gz'
    def build(link=False):
        with tarfile.open(path, 'w:gz') as archive:
            content = {f'{ROOT}/src/nutev/{name}': b'# synthetic module' for name in ('__init__.py', 'cli.py', '__version__.py')}
            content[f'{ROOT}/PKG-INFO'] = f'Name: nutev-nutmev\nVersion: {VERSION}\n'.encode()
            for name, body in content.items():
                info = tarfile.TarInfo(name)
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
            if link:
                info = tarfile.TarInfo(f'{ROOT}/src/nutev/link.py')
                info.type = tarfile.LNKTYPE
                info.linkname = '/etc/passwd'
                archive.addfile(info)
    build()
    assert audit_distribution(path, VERSION)['status'] == 'PASS'
    build(True)
    with pytest.raises(ValueError):
        audit_distribution(path, VERSION)


def test_candidate_metadata_and_container_gate_are_synchronized():
    import json
    import tomllib
    import yaml
    from nutev.__version__ import __version__
    root = Path(__file__).resolve().parents[1]
    assert __version__ == VERSION
    zenodo = json.loads((root / '.zenodo.json').read_text())
    assert zenodo['version'] == VERSION
    assert zenodo['publication_date'] == RELEASE_DATE
    assert DOI in zenodo['notes']
    cff = yaml.safe_load((root / 'CITATION.cff').read_text())
    assert cff['version'] == cff['preferred-citation']['version'] == VERSION
    assert cff['doi'] == cff['preferred-citation']['doi'] == DOI
    assert str(cff['date-released']) == RELEASE_DATE
    assert str(cff['preferred-citation']['date-released']) == RELEASE_DATE
    build = tomllib.loads((root / 'pyproject.toml').read_text())['tool']['pdm']['build']
    assert build['includes'] == ['src/nutev/**/*.py']
    workflow = (root / '.github/workflows/release-artifact-validation.yml').read_text()
    assert 'python tools/audit_public_package.py' in workflow
    assert 'bash tools/run_container_release_gate.sh' in workflow
