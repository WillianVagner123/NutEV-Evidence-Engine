"""Inspect built Python distributions without extracting untrusted members.

This gate checks archive structure, identity and specific forbidden content.
It does not certify copyright, personal-data absence or scientific validity.
"""
from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile
import zipfile

MAX_FILES = 10000
MAX_MEMBER_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 150 * 1024 * 1024
PRIVATE_PARTS = {'private_data', 'backup', 'backups', '.git', '.venv',
                 'browser_e2e_artifacts', 'closeout_artifacts'}
PRIVATE_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.pem', '.key', '.p12', '.pfx', '.pdf'}
METADATA_NAMES = {'LICENSE', 'README.md', 'NOTICE.md', 'CITATION.cff', 'pyproject.toml', 'PKG-INFO'}


def check_name(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (path.is_absolute() or '..' in path.parts or '\\' in name or not name
            or ':' in name or any(ord(c) < 32 for c in name)
            or path.as_posix() != name.rstrip('/')):
        raise ValueError('noncanonical archive path')
    for part in path.parts:
        if (part in PRIVATE_PARTS or part.startswith(('project_output', '.env'))
                or part.endswith(('-wal', '-shm', '-journal'))):
            raise ValueError('private runtime path in package')
    if path.suffix.lower() in PRIVATE_SUFFIXES:
        raise ValueError('forbidden package file type')
    return path


def _entries(path: Path):
    if path.suffix == '.whl':
        with zipfile.ZipFile(path) as archive:
            for item in archive.infolist():
                if item.is_dir():
                    check_name(item.filename)
                    continue
                mode = item.external_attr >> 16
                if stat.S_ISLNK(mode) or item.flag_bits & 1:
                    raise ValueError('symlink or encrypted member')
                if item.file_size > MAX_MEMBER_BYTES:
                    raise ValueError('oversized archive member')
                yield item.filename, archive.read(item)
    elif path.name.endswith('.tar.gz'):
        with tarfile.open(path, 'r:gz') as archive:
            for item in archive:
                if item.isdir():
                    check_name(item.name)
                    continue
                if not item.isfile() or item.size > MAX_MEMBER_BYTES:
                    raise ValueError('nonregular or oversized archive member')
                stream = archive.extractfile(item)
                if stream is None:
                    raise ValueError('missing member bytes')
                yield item.name, stream.read(MAX_MEMBER_BYTES + 1)
    else:
        raise ValueError('unsupported distribution format')


def audit_distribution(path: Path, version: str) -> dict:
    if not version or any(c not in '0123456789abcdefghijklmnopqrstuvwxyz.' for c in version):
        raise ValueError('invalid expected version')
    wheel = path.suffix == '.whl'
    expected_root = f'nutev_nutmev-{version}'
    metadata_path = f'{expected_root}.dist-info/METADATA' if wheel else f'{expected_root}/PKG-INFO'
    inventory = []
    seen = set()
    total = 0
    metadata = None
    package_modules = set()
    for name, body in _entries(path):
        parts = check_name(name).parts
        if name in seen:
            raise ValueError('duplicate archive member')
        seen.add(name)
        total += len(body)
        if len(seen) > MAX_FILES or total > MAX_TOTAL_BYTES or len(body) > MAX_MEMBER_BYTES:
            raise ValueError('archive size limit')
        if wheel:
            allowed = (parts[0] == 'nutev' and name.endswith('.py')) or parts[0] == expected_root + '.dist-info'
            module = name
        else:
            if parts[0] != expected_root:
                raise ValueError('unexpected source distribution root')
            relative = PurePosixPath(*parts[1:]).as_posix()
            allowed = (relative.startswith('src/nutev/') and relative.endswith('.py')) or relative in METADATA_NAMES
            module = relative.removeprefix('src/')
        if not allowed:
            raise ValueError('member outside distribution allowlist')
        # Construct markers so this verifier's source is not itself a private key.
        if (b'SQLite format 3\x00' in body or b'NUTEV_PACKAGE_PRIVATE_' + b'CANARY' in body
                or any(b'-----BEGIN ' + prefix + b'PRIVATE KEY-----' in body
                       for prefix in (b'', b'RSA ', b'EC ', b'OPENSSH '))):
            raise ValueError('forbidden embedded content')
        package_modules.add(module)
        if name == metadata_path:
            metadata = BytesParser().parsebytes(body)
        inventory.append({'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()})
    if not {'nutev/__init__.py', 'nutev/cli.py', 'nutev/__version__.py'} <= package_modules:
        raise ValueError('missing required Python modules')
    if metadata is None or metadata['Name'] != 'nutev-nutmev' or metadata['Version'] != version:
        raise ValueError('distribution metadata mismatch')
    return {'status': 'PASS', 'filename': path.name, 'version': version,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size,
            'members': inventory, 'scope': 'Python library and CLI only; no production-data acceptance'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    candidates = sorted(args.dist.glob('*.whl')) + sorted(args.dist.glob('*.tar.gz'))
    try:
        if len(candidates) != 2 or len(list(args.dist.glob('*.whl'))) != 1:
            raise ValueError('exactly one wheel and one sdist required')
        reports = [audit_distribution(path, args.version) for path in candidates]
        report = {'status': 'PASS', 'artifacts': reports, 'production_deployed': False, 'published': False}
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        report = {'status': 'FAIL', 'reason': str(exc), 'published': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'artifacts'}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
