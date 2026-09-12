from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

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


class FakeDocker:
    def __init__(self, *, images: set[str], in_use: set[str] | None = None):
        self.images = set(images)
        self.in_use = set(in_use or set())
        self.calls: list[list[str]] = []

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(command)
        if command[:3] == ["docker", "image", "ls"]:
            ref = command[-1]
            stdout = f"sha256:{ref.removeprefix('nutev:')}\n" if ref in self.images else ""
            return subprocess.CompletedProcess(command, 0, stdout, "")
        if command[:2] == ["docker", "ps"]:
            ref = command[-1].removeprefix("ancestor=")
            stdout = "container-id\n" if ref in self.in_use else ""
            return subprocess.CompletedProcess(command, 0, stdout, "")
        if command[:3] == ["docker", "image", "rm"]:
            ref = command[-1]
            if ref not in self.images:
                return subprocess.CompletedProcess(command, 1, "", "missing")
            self.images.remove(ref)
            return subprocess.CompletedProcess(command, 0, f"Untagged: {ref}\n", "")
        if command[:3] == ["docker", "image", "prune"]:
            return subprocess.CompletedProcess(command, 0, "Total reclaimed space: 0B\n", "")
        raise AssertionError(f"unexpected docker command: {command}")


def test_allowlisted_incomplete_recovery_is_pruned(tmp_path: Path) -> None:
    doomed = _recovery(tmp_path, FAILED)
    (doomed / "partial.bin").write_bytes(b"partial")

    report = HYGIENE.prune_incomplete(tmp_path, allowed_failed_shas={FAILED})

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
    with pytest.raises(ValueError, match="invalid SHA"):
        HYGIENE.prune_failed_images({"main"}, runner=FakeDocker(images=set()))


def test_excluded_directory_is_never_deleted(tmp_path: Path) -> None:
    path = _recovery(tmp_path, FAILED)

    report = HYGIENE.prune_incomplete(
        tmp_path,
        allowed_failed_shas={FAILED},
        exclude=path,
    )

    assert report["pruned_incomplete"] == 0
    assert path.exists()


def test_only_allowlisted_unused_failed_image_tag_is_removed() -> None:
    failed_ref = f"nutev:{FAILED}"
    other_ref = f"nutev:{OTHER}"
    docker = FakeDocker(images={failed_ref, other_ref})

    report = HYGIENE.prune_failed_images({FAILED}, runner=docker)

    assert report["removed_failed_image_tags"] == 1
    assert failed_ref not in docker.images
    assert other_ref in docker.images
    assert report["dangling_image_prune"] == "PASS"
    assert ["docker", "image", "rm", other_ref] not in docker.calls


def test_failed_image_used_by_any_container_is_preserved() -> None:
    failed_ref = f"nutev:{FAILED}"
    docker = FakeDocker(images={failed_ref}, in_use={failed_ref})

    report = HYGIENE.prune_failed_images({FAILED}, runner=docker)

    assert report["preserved_failed_images_in_use"] == 1
    assert report["removed_failed_image_tags"] == 0
    assert failed_ref in docker.images
    assert ["docker", "image", "rm", failed_ref] not in docker.calls


def test_absent_failed_image_is_a_safe_noop() -> None:
    docker = FakeDocker(images=set())

    report = HYGIENE.prune_failed_images({FAILED}, runner=docker)

    assert report["absent_failed_image_tags"] == 1
    assert report["removed_failed_image_tags"] == 0


def test_docker_lookup_failure_fails_closed() -> None:
    def broken(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, "", "daemon unavailable")

    with pytest.raises(RuntimeError, match="lookup failed"):
        HYGIENE.prune_failed_images({FAILED}, runner=broken)
