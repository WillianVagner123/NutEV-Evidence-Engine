"""Integrity includes directory structure and permissions, not only file bytes."""
import os
import stat
from pathlib import Path

import pytest

from tools.recovery_snapshot import create_snapshot, rehearse_restore, validate_snapshot


def _snapshot(tmp_path):
    source = tmp_path / 'source'
    (source / 'empty').mkdir(parents=True)
    (source / 'record.txt').write_text('synthetic private record')
    (source / 'record.txt').chmod(0o600)
    backup = tmp_path / 'backup'
    create_snapshot(source, backup, quiesced=True)
    return source, backup


def test_empty_directory_removal_is_detected(tmp_path):
    _, backup = _snapshot(tmp_path)
    (backup / 'files' / 'empty').rmdir()
    with pytest.raises(ValueError):
        validate_snapshot(backup)


def test_new_empty_directory_is_detected(tmp_path):
    _, backup = _snapshot(tmp_path)
    (backup / 'files' / 'unexpected').mkdir()
    with pytest.raises(ValueError):
        validate_snapshot(backup)


def test_permission_tampering_is_detected(tmp_path):
    _, backup = _snapshot(tmp_path)
    (backup / 'files' / 'record.txt').chmod(0o644)
    with pytest.raises(ValueError):
        validate_snapshot(backup)


def test_restored_tree_retains_structure_and_permissions(tmp_path):
    source, backup = _snapshot(tmp_path)
    dest = tmp_path / 'restore'
    report = rehearse_restore(backup, dest)
    assert report['filesystem_metadata_verified'] is True
    assert (dest / 'empty').is_dir()
    assert stat.S_IMODE((dest / 'record.txt').stat().st_mode) == 0o600
    assert (dest / 'record.txt').stat().st_uid == (source / 'record.txt').stat().st_uid
    assert stat.S_IMODE((backup / 'restore-proof.json').stat().st_mode) == 0o600


def test_file_ownership_tampering_is_detected(tmp_path, monkeypatch):
    _, backup = _snapshot(tmp_path)
    real_stat = Path.lstat
    target = backup / 'files' / 'record.txt'
    def different_owner(path):
        value = real_stat(path)
        if path != target:
            return value
        values = list(value)
        values[4] = value.st_uid + 1
        return os.stat_result(values)
    monkeypatch.setattr(Path, 'lstat', different_owner)
    with pytest.raises(ValueError):
        validate_snapshot(backup)
