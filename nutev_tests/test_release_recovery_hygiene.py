from __future__ import annotations

import importlib.util
import json
import os
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
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

FAILED = "a" * 40
OTHER = "b" * 40
THIRD = "c" * 40
ACTIVE = "d" * 40
FIFTH = "e" * 40


def _recovery(base: Path, sha: str, suffix: str = "abcdef") -> Path:
    path = base / f"{sha}.{suffix}"
    path.mkdir(parents=True)
    return path


def _complete(path: Path, *, completed_ns: int | None = None) -> None:
    volume = path / "volume"
    volume.mkdir()
    (volume / "manifest.json").write_text(
        json.dumps({"type": "NUTEV_QUIESCED_SNAPSHOT", "version": 2}),
        encoding="utf-8",
    )
    proof = volume / "restore-proof.json"
    proof.write_text(
        json.dumps({"status": "PASS", "production_overwritten": False}),
        encoding="utf-8",
    )
    if completed_ns is not None:
        os.utime(proof, ns=(completed_ns, completed_ns))


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


def test_complete_snapshot_is_preserved_by_default_even_when_allowlisted(tmp_path: Path) -> None:
    path = _recovery(tmp_path, FAILED)
    _complete(path)

    report = HYGIENE.prune_incomplete(tmp_path, allowed_failed_shas={FAILED})

    assert report["preserved_complete"] == 1
    assert report["pruned_complete"] == 0
    assert report["pruned_incomplete"] == 0
    assert path.exists()


def test_complete_retention_never_prunes_without_deploy_history_allowlist(tmp_path: Path) -> None:
    paths = []
    for index, sha in enumerate((FAILED, OTHER, THIRD, ACTIVE), start=1):
        path = _recovery(tmp_path, sha, f"keep{index:02d}")
        _complete(path, completed_ns=index * 1_000_000_000)
        paths.append(path)

    report = HYGIENE.prune_incomplete(
        tmp_path,
        allowed_failed_shas=set(),
        retain_complete=3,
        protected_shas={ACTIVE},
        allowed_complete_prune_shas=set(),
    )

    assert report["pruned_complete"] == 0
    assert report["preserved_complete"] == 4
    assert all(path.exists() for path in paths)


def test_complete_retention_prunes_only_oldest_eligible_and_keeps_three(tmp_path: Path) -> None:
    snapshots: dict[str, Path] = {}
    for index, sha in enumerate((FAILED, OTHER, THIRD, ACTIVE), start=1):
        path = _recovery(tmp_path, sha, f"snap{index:02d}")
        _complete(path, completed_ns=index * 1_000_000_000)
        snapshots[sha] = path

    report = HYGIENE.prune_incomplete(
        tmp_path,
        allowed_failed_shas=set(),
        retain_complete=3,
        protected_shas={ACTIVE},
        allowed_complete_prune_shas={FAILED, OTHER, THIRD},
    )

    assert report["pruned_complete"] == 1
    assert report["preserved_complete"] == 3
    assert report["protected_complete"] == 1
    assert not snapshots[FAILED].exists()
    assert snapshots[OTHER].exists()
    assert snapshots[THIRD].exists()
    assert snapshots[ACTIVE].exists()


def test_protected_complete_is_never_pruned_even_if_oldest_and_eligible(tmp_path: Path) -> None:
    snapshots: dict[str, Path] = {}
    for index, sha in enumerate((ACTIVE, FAILED, OTHER, THIRD), start=1):
        path = _recovery(tmp_path, sha, f"protect{index:02d}")
        _complete(path, completed_ns=index * 1_000_000_000)
        snapshots[sha] = path

    report = HYGIENE.prune_incomplete(
        tmp_path,
        allowed_failed_shas=set(),
        retain_complete=3,
        protected_shas={ACTIVE},
        allowed_complete_prune_shas={ACTIVE, FAILED, OTHER, THIRD},
    )

    assert report["pruned_complete"] == 1
    assert snapshots[ACTIVE].exists()
    assert not snapshots[FAILED].exists()
    assert snapshots[OTHER].exists()
    assert snapshots[THIRD].exists()


def test_complete_retention_never_drops_below_configured_floor(tmp_path: Path) -> None:
    snapshots = []
    for index, sha in enumerate((FAILED, OTHER, THIRD, ACTIVE, FIFTH), start=1):
        path = _recovery(tmp_path, sha, f"floor{index:02d}")
        _complete(path, completed_ns=index * 1_000_000_000)
        snapshots.append(path)

    report = HYGIENE.prune_incomplete(
        tmp_path,
        allowed_failed_shas=set(),
        retain_complete=3,
        protected_shas={ACTIVE},
        allowed_complete_prune_shas={FAILED, OTHER, THIRD, FIFTH},
    )

    assert report["pruned_complete"] == 2
    assert report["preserved_complete"] == 3
    assert sum(path.exists() for path in snapshots) == 3


def test_complete_prune_allowlist_requires_retention_floor(tmp_path: Path) -> None:
    path = _recovery(tmp_path, FAILED)
    _complete(path)

    with pytest.raises(ValueError, match="requires retain-complete"):
        HYGIENE.prune_incomplete(
            tmp_path,
            allowed_failed_shas=set(),
            allowed_complete_prune_shas={FAILED},
        )
    assert path.exists()


def test_invalid_complete_retention_inputs_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="retain-complete"):
        HYGIENE.prune_incomplete(
            tmp_path,
            allowed_failed_shas=set(),
            retain_complete=0,
        )
    with pytest.raises(ValueError, match="complete-snapshot prune allowlist"):
        HYGIENE.prune_incomplete(
            tmp_path,
            allowed_failed_shas=set(),
            retain_complete=3,
            allowed_complete_prune_shas={"main"},
        )
    with pytest.raises(ValueError, match="protected snapshot allowlist"):
        HYGIENE.prune_incomplete(
            tmp_path,
            allowed_failed_shas=set(),
            retain_complete=3,
            protected_shas={"main"},
        )


def test_suspicious_snapshot_is_preserved(tmp_path: Path) -> None:
    path = _recovery(tmp_path, FAILED)
    volume = path / "volume"
    volume.mkdir()
    (volume / "manifest.json").write_text("{broken", encoding="utf-8")
    (volume / "restore-proof.json").write_text("{}", encoding="utf-8")

    report = HYGIENE.prune_incomplete(
        tmp_path,
        allowed_failed_shas={FAILED},
        retain_complete=3,
        allowed_complete_prune_shas={FAILED},
    )

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


def test_builder_cache_prune_is_explicit_and_scoped_to_build_cache() -> None:
    calls: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "Total reclaimed space: 256MB\n", "")

    report = HYGIENE.prune_builder_cache(runner=runner)

    assert report == {"builder_cache_prune": "PASS"}
    assert calls == [["docker", "builder", "prune", "-a", "-f"]]
    flattened = " ".join(calls[0])
    assert "system prune" not in flattened
    assert "volume prune" not in flattened
    assert "image prune" not in flattened


def test_builder_cache_prune_failure_fails_closed() -> None:
    def broken(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, "", "builder unavailable")

    with pytest.raises(RuntimeError, match="builder-cache prune failed"):
        HYGIENE.prune_builder_cache(runner=broken)


def test_main_recovery_readiness_explicitly_opts_into_builder_cache_prune() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "--prune-builder-cache" in text
    assert "--retain-complete 3" in text
    assert "docker system prune" not in text
    assert "docker volume prune" not in text
