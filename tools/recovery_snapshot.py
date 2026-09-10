"""Lossless snapshot + restore rehearsal of a QUIESCED output tree.

Never restores over production. Caller must stop writers first. Backup and
rehearsal destinations must be new, outside source, on protected storage.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import tempfile


def inventory(root: Path) -> dict:
    result={}
    for p in sorted(root.rglob('*')):
        mode=p.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError('unsafe filesystem entry')
        if p.is_file():
            digest=hashlib.sha256()
            with p.open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
            result[p.relative_to(root).as_posix()]={'bytes':p.stat().st_size,'sha256':digest.hexdigest()}
    return result


def safe_destination(source: Path,dest: Path) -> None:
    if source.is_symlink() or dest.is_symlink():raise ValueError('symlink root')
    source=source.resolve();dest=dest.resolve()
    if dest==source or source in dest.parents or dest in source.parents:
        raise ValueError('overlapping source and destination')
    if dest.exists():raise ValueError('destination must not exist')
    if not source.is_dir():raise ValueError('source directory required')


def validate_snapshot(backup: Path) -> dict:
    if backup.is_symlink() or (backup/'files').is_symlink() or (backup/'manifest.json').is_symlink():raise ValueError('symlink snapshot')
    if not (backup/'files').is_dir():raise ValueError('snapshot files directory required')
    manifest=json.loads((backup/'manifest.json').read_text())
    if manifest.get('type')!='NUTEV_QUIESCED_SNAPSHOT' or manifest.get('version')!=1:
        raise ValueError('unknown snapshot schema')
    for name in manifest['files']:
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError('unsafe manifest path')
    if inventory(backup/'files')!=manifest['files']:raise ValueError('snapshot integrity mismatch')
    return manifest


def database_checks(root: Path) -> list:
    checks=[]
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        with path.open('rb') as stream:header=stream.read(16)
        if header!=b'SQLite format 3\x00':continue
        # Operate only on the restored isolated copy; recover WAL there, never in source.
        with sqlite3.connect(path) as con:
            if con.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('database integrity failure')
            if con.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('database foreign key failure')
            names=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            counts={n:con.execute('SELECT count(*) FROM "'+n.replace('"','""')+'"').fetchone()[0] for n in names}
            checks.append({'path':path.relative_to(root).as_posix(),'integrity':'ok','row_counts':counts})
    return checks


def rehearse_restore(backup: Path,destination: Path) -> dict:
    manifest=validate_snapshot(backup)
    safe_destination(backup,destination)
    shutil.copytree(backup/'files',destination)
    if inventory(destination)!=manifest['files']:raise ValueError('restore byte mismatch')
    return {'status':'PASS','files_verified':len(manifest['files']),'databases':database_checks(destination),
            'production_overwritten':False}


def create_snapshot(source: Path,backup: Path,*,quiesced: bool=False) -> dict:
    if not quiesced:raise ValueError('writers must be stopped before snapshot')
    safe_destination(source,backup)
    before=inventory(source)
    backup.mkdir(parents=True,mode=0o700)
    shutil.copytree(source,backup/'files',symlinks=False)
    if inventory(source)!=before or inventory(backup/'files')!=before:
        raise ValueError('source changed during snapshot; no consistent backup produced')
    manifest={'type':'NUTEV_QUIESCED_SNAPSHOT','version':1,'writers_stopped_by_caller':True,'files':before}
    path=backup/'manifest.json';path.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n');path.chmod(0o600)
    with tempfile.TemporaryDirectory(prefix='nutev-restore-proof-',dir=backup.parent) as temp:
        proof=rehearse_restore(backup,Path(temp)/'restored')
    (backup/'restore-proof.json').write_text(json.dumps(proof,sort_keys=True,indent=2)+'\n')
    # Do not print private paths, table names, or file contents in CI/deploy logs.
    return {'status':'PASS','files_verified':proof['files_verified'],'databases_verified':len(proof['databases']),
            'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'production_overwritten':False}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--backup',type=Path,required=True)
    parser.add_argument('--quiesced',action='store_true')
    args=parser.parse_args()
    print(json.dumps(create_snapshot(args.source,args.backup,quiesced=args.quiesced),sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
