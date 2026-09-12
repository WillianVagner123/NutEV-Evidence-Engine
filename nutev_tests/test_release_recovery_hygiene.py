from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "release_recovery_hygiene", ROOT / "tools/release_recovery_hygiene.py"
)
assert SPEC and SPEC.loader
HYGIENE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HYGIENE)

FAILED = "a" * 40
OTHER = "b" * 40


def _recovery(base: Path, sha: str, suffix: str = "abcdef") -> Path:
    path = base / f"{sha}.{suffix}"
    path.mkdir(parents=True)
    return path


def _complete(path: Path) -> None:
    volume = path / "volume"
    volume.mkdir()
    (volume / "manifest.json").write_text(
        json.dumps({"type": "NUTEV_QUIESCED_SNAPSHOT", "version": 2}),
        encoding="utf-8",
    )
    (volume / "restore-proof.json").write_text(
        json.dumps({"status": "PASS", "production_overwritten": False}),
        encoding="utf-8",
    )


def test_allowlisted_incomplete_recovery_is_pruned(tmp_path: Path) -> None:
    doomed = _recovery(tmp_path, FAILED)
    (doomed / "partial.bin").write_bytes(b"partial")

    report = HYGIENE.prune_incomplete(tmp_path, allowed_failed_shas={FAILED})

    assert report["status"] == "PASS"
    assert report["pruned_incomplete"] == 1
    assert not doomed.exists()


def test_unapproved_incomplete_recovery_is_preserved(tmp_path: Path) -> None:
    path = _recovery(tmp_path, OTHER)
    (path / "partial.bin").write_bytes(b"partial")

    report = HYGIENE.prune_incomplete(tmp_path, allowed_failed_shas={FAILED})

    assert report["preserved_unapproved"] == 1
    assert path.exists()


def test_complete_snapshot_is_preserved_even_when_allowlisted(tmp_path: Path) -> None:
    path = _recovery(tmp_path, FAILED)
    _complete(path)

    report = HYGIENE.prune_incomplete(tmp_path, allowed_failed_shas={FAILED})

    assert report["preserved_complete"] == 1
    assert report["pruned_incomplete"] == 0
    assert path.exists()


def test_suspicious_snapshot_is_preserved(tmp_path: Path) -> None:
    path = _recovery(tmp_path, FAILED)
    volume = path / "volume"
    volume.mkdir()
    (volume / "manifest.json").write_text("{broken", encoding="utf-8")
    (volume / "restore-proof.json").write_text("{}", encoding="utf-8")

    report = HYGIENE.prune_incomplete(tmp_path, allowed_failed_shas={FAILED})

    assert report["preserved_suspicious"] == 1
    assert path.exists()


def test_unknown_name_and_symlink_are_never_deleted(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-recovery"
    outside.mkdir(exist_ok=True)
    unknown = tmp_path / "manual-note"
    unknown.mkdir()
    link = tmp_path / f"{FAILED}.symlink1"
    link.symlink_to(outside, target_is_directory=True)

    report = HYGIENE.prune_incomplete(tmp_path, allowed_failed_shas={FAILED})

    assert report["skipped_unknown"] == 2
    assert unknown.exists()
    assert link.is_symlink()
    assert outside.exists()


def test_invalid_allowlist_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid SHA"):
        HYGIENE.prune_incomplete(tmp_path, allowed_failed_shas={"main"})


def test_excluded_directory_is_never_deleted(tmp_path: Path) -> None:
    path = _recovery(tmp_path, FAILED)

    report = HYGIENE.prune_incomplete(
        tmp_path,
        allowed_failed_shas={FAILED},
        exclude=path,
    )

    assert report["pruned_incomplete"] == 0
    assert path.exists()
