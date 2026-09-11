import json
import sqlite3
import pytest
from tools.recovery_snapshot import create_snapshot,rehearse_restore,validate_snapshot


def source(tmp_path):
    root=tmp_path/'source';root.mkdir()
    with sqlite3.connect(root/'fixture.sqlite') as con:
        con.execute('CREATE TABLE decisions(id PRIMARY KEY, decision TEXT)')
        con.execute("INSERT INTO decisions VALUES(1,'human fixture preserved')")
    (root/'notes.txt').write_text('private fixture only')
    return root


def test_snapshot_restores_counts_and_bytes(tmp_path):
    root=source(tmp_path);dest=tmp_path/'backup'
    assert create_snapshot(root,dest,quiesced=True)['status']=='PASS'
    proof=rehearse_restore(dest,tmp_path/'restore')
    assert proof['databases'][0]['row_counts']['decisions']==1
    assert (tmp_path/'restore/notes.txt').read_bytes()==(root/'notes.txt').read_bytes()


def test_wal_is_preserved(tmp_path):
    root=source(tmp_path);con=sqlite3.connect(root/'fixture.sqlite')
    try:
        con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA wal_autocheckpoint=0')
        con.execute("INSERT INTO decisions VALUES(2,'committed WAL fixture')");con.commit()
        assert (root/'fixture.sqlite-wal').exists()
        # No concurrent writer during snapshot; an idle reader keeps WAL alive.
        create_snapshot(root,tmp_path/'backup',quiesced=True)
        proof=rehearse_restore(tmp_path/'backup',tmp_path/'restore')
        assert proof['databases'][0]['row_counts']['decisions']==2
    finally:con.close()


def test_requires_quiescence(tmp_path):
    with pytest.raises(ValueError):create_snapshot(source(tmp_path),tmp_path/'backup')


@pytest.mark.parametrize('entry',['notes.txt','extra.txt'])
def test_tamper_or_unlisted_files_rejected(tmp_path,entry):
    root=source(tmp_path);backup=tmp_path/'backup';create_snapshot(root,backup,quiesced=True)
    (backup/'files'/entry).write_text('tamper')
    with pytest.raises(ValueError):validate_snapshot(backup)


def test_no_overwrite_or_nested_destination(tmp_path):
    root=source(tmp_path)
    for dest in [root,root/'backup',tmp_path]:
        with pytest.raises(ValueError):create_snapshot(root,dest,quiesced=True)


def test_symlink_rejected(tmp_path):
    root=source(tmp_path);(root/'link').symlink_to(root/'notes.txt')
    with pytest.raises(ValueError):create_snapshot(root,tmp_path/'backup',quiesced=True)


def test_manifest_traversal_rejected(tmp_path):
    root=source(tmp_path);backup=tmp_path/'backup';create_snapshot(root,backup,quiesced=True)
    p=backup/'manifest.json';m=json.loads(p.read_text());m['files']['../outside']={};p.write_text(json.dumps(m))
    with pytest.raises(ValueError):rehearse_restore(backup,tmp_path/'restore')
