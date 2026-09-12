"""Conservative hygiene for NutEV release-recovery state.

Canonical incomplete recovery directories are removed only when their target SHA
belongs to an explicitly approved failed-deploy allowlist. Complete snapshots,
suspicious/corrupt-looking directories, unknown names and symlinks are preserved
by default.

Production may opt into bounded complete-snapshot retention with
``--retain-complete`` plus one or more ``--prune-complete-sha`` values. Even then,
a complete snapshot is removable only when its target SHA is explicitly backed by
trusted deployment history, the snapshot still passes the complete proof, its SHA
is not protected, and at least the configured number of complete rollback points
remain. Scientific output volumes are never touched.

The CLI also reclaims Docker image tags only when they are named ``nutev:<SHA>``,
the SHA is in the failed-deploy allowlist, and no running or stopped container
references the image. A final ordinary ``docker image prune`` removes only
dangling, unused images. Bounded production retention also reclaims unused Docker
builder cache; callers outside bounded retention may opt in with
``--prune-builder-cache``. This invokes only ``docker builder prune -a -f`` and
never prunes containers, runtime images, networks or volumes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Callable

RECOVERY_NAME = re.compile(r"^([0-9a-f]{40})\.([A-Za-z0-9_-]{6,})$")
SHA = re.compile(r"^[0-9a-f]{40}$")
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _complete_snapshot(directory: Path) -> bool | None:
    """Return True for a valid complete recovery, False for missing markers.

    Return None when both markers exist but cannot be trusted/parsed; callers
    preserve these directories rather than deleting potentially useful evidence.
    """
    manifest = directory / "volume" / "manifest.json"
    proof = directory / "volume" / "restore-proof.json"
    if not _regular_file(manifest) or not _regular_file(proof):
        return False
    try:
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        proof_data = json.loads(proof.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if (
        manifest_data.get("type") == "NUTEV_QUIESCED_SNAPSHOT"
        and manifest_data.get("version") == 2
        and proof_data.get("status") == "PASS"
        and proof_data.get("production_overwritten") is False
    ):
        return True
    return None


def _complete_order(directory: Path) -> tuple[int, str]:
    """Return a deterministic completion order for a proven-complete snapshot."""
    proof = directory / "volume" / "restore-proof.json"
    if not _regular_file(proof):
        raise ValueError("complete snapshot lost its restore proof during retention")
    try:
        completed_ns = proof.stat().st_mtime_ns
    except OSError as exc:
        raise ValueError("complete snapshot restore proof cannot be stat'ed") from exc
    return completed_ns, directory.name


def _validated_allowlist(values: set[str], *, label: str = "failed-deploy allowlist") -> set[str]:
    if any(not SHA.fullmatch(value) for value in values):
        raise ValueError(f"{label} contains an invalid SHA")
    return values


def prune_incomplete(
    base: Path,
    *,
    allowed_failed_shas: set[str],
    exclude: Path | None = None,
    retain_complete: int | None = None,
    protected_shas: set[str] | None = None,
    allowed_complete_prune_shas: set[str] | None = None,
) -> dict:
    allowed_failed_shas = _validated_allowlist(set(allowed_failed_shas))
    protected_shas = _validated_allowlist(
        set(protected_shas or set()), label="protected snapshot allowlist"
    )
    allowed_complete_prune_shas = _validated_allowlist(
        set(allowed_complete_prune_shas or set()),
        label="complete-snapshot prune allowlist",
    )
    if retain_complete is not None and retain_complete < 1:
        raise ValueError("retain-complete must be at least 1")
    if retain_complete is None and allowed_complete_prune_shas:
        raise ValueError("complete-snapshot prune allowlist requires retain-complete")

    base.mkdir(parents=True, exist_ok=True)
    if base.is_symlink() or not base.is_dir():
        raise ValueError("recovery base must be a real directory")
    base_resolved = base.resolve()
    excluded = exclude.resolve() if exclude is not None else None
    if excluded is not None and excluded.parent != base_resolved:
        raise ValueError("excluded recovery directory must be inside recovery base")

    pruned = 0
    pruned_complete = 0
    preserved_suspicious = 0
    preserved_unapproved = 0
    skipped_unknown = 0
    complete: list[tuple[Path, str]] = []

    for entry in sorted(base.iterdir(), key=lambda item: item.name):
        if entry.is_symlink() or not entry.is_dir():
            skipped_unknown += 1
            continue
        resolved = entry.resolve()
        if resolved.parent != base_resolved:
            skipped_unknown += 1
            continue
        if excluded is not None and resolved == excluded:
            continue
        match = RECOVERY_NAME.fullmatch(entry.name)
        if match is None:
            skipped_unknown += 1
            continue

        target_sha = match.group(1)
        state = _complete_snapshot(entry)
        if state is True:
            complete.append((entry, target_sha))
            continue
        if state is None:
            preserved_suspicious += 1
            continue
        if target_sha not in allowed_failed_shas:
            preserved_unapproved += 1
            continue

        shutil.rmtree(entry)
        pruned += 1

    retained_complete = {entry for entry, _sha in complete}
    if retain_complete is not None and len(complete) > retain_complete:
        removable = [
            (entry, target_sha)
            for entry, target_sha in complete
            if target_sha in allowed_complete_prune_shas
            and target_sha not in protected_shas
        ]
        removable.sort(key=lambda item: _complete_order(item[0]))
        removal_budget = max(0, len(complete) - retain_complete)
        for entry, _target_sha in removable[:removal_budget]:
            if _complete_snapshot(entry) is not True:
                raise ValueError("snapshot changed during complete-retention pruning")
            shutil.rmtree(entry)
            retained_complete.remove(entry)
            pruned_complete += 1

    return {
        "pruned_incomplete": pruned,
        "pruned_complete": pruned_complete,
        "preserved_complete": len(retained_complete),
        "protected_complete": sum(
            1 for entry, sha in complete if entry in retained_complete and sha in protected_shas
        ),
        "retain_complete": retain_complete,
        "eligible_complete_prune_sha_count": len(allowed_complete_prune_shas),
        "preserved_suspicious": preserved_suspicious,
        "preserved_unapproved": preserved_unapproved,
        "skipped_unknown": skipped_unknown,
    }


def _subprocess_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def prune_failed_images(
    allowed_failed_shas: set[str],
    *,
    runner: Runner = _subprocess_runner,
) -> dict:
    """Remove only unused ``nutev:<failed-sha>`` tags and dangling images."""
    allowed_failed_shas = _validated_allowlist(set(allowed_failed_shas))
    removed_failed_tags = 0
    preserved_in_use = 0
    absent_failed_tags = 0

    for sha in sorted(allowed_failed_shas):
        image_ref = f"nutev:{sha}"
        listed = runner(["docker", "image", "ls", "--quiet", "--no-trunc", image_ref])
        if listed.returncode != 0:
            raise RuntimeError(f"docker image lookup failed for approved SHA {sha}")
        image_ids = {line.strip() for line in listed.stdout.splitlines() if line.strip()}
        if not image_ids:
            absent_failed_tags += 1
            continue
        if len(image_ids) != 1:
            raise RuntimeError(f"ambiguous docker image identity for approved SHA {sha}")

        containers = runner(["docker", "ps", "-aq", "--filter", f"ancestor={image_ref}"])
        if containers.returncode != 0:
            raise RuntimeError(f"docker container lookup failed for approved SHA {sha}")
        if containers.stdout.strip():
            preserved_in_use += 1
            continue

        removed = runner(["docker", "image", "rm", image_ref])
        if removed.returncode != 0:
            raise RuntimeError(f"docker image removal failed for approved SHA {sha}")
        removed_failed_tags += 1

    dangling = runner(["docker", "image", "prune", "-f"])
    if dangling.returncode != 0:
        raise RuntimeError("docker dangling-image prune failed")

    return {
        "removed_failed_image_tags": removed_failed_tags,
        "preserved_failed_images_in_use": preserved_in_use,
        "absent_failed_image_tags": absent_failed_tags,
        "dangling_image_prune": "PASS",
    }


def prune_builder_cache(*, runner: Runner = _subprocess_runner) -> dict:
    """Reclaim only unused Docker build cache; never prune runtime objects."""
    command = ["docker", "builder", "prune", "-a", "-f"]
    result = runner(command)
    if result.returncode != 0:
        raise RuntimeError("docker builder-cache prune failed")
    return {"builder_cache_prune": "PASS"}


def should_prune_builder_cache(*, retain_complete: int | None, explicitly_requested: bool) -> bool:
    """Bounded production retention is itself an explicit hygiene opt-in."""
    return explicitly_requested or retain_complete is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--exclude", type=Path)
    parser.add_argument("--allow-sha", action="append", default=[])
    parser.add_argument("--protect-sha", action="append", default=[])
    parser.add_argument("--prune-complete-sha", action="append", default=[])
    parser.add_argument("--retain-complete", type=int)
    parser.add_argument("--prune-builder-cache", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    allowed_failed_shas = set(args.allow_sha)
    protected_shas = set(args.protect_sha)
    allowed_complete_prune_shas = set(args.prune_complete_sha)
    try:
        recovery = prune_incomplete(
            args.base,
            allowed_failed_shas=allowed_failed_shas,
            exclude=args.exclude,
            retain_complete=args.retain_complete,
            protected_shas=protected_shas,
            allowed_complete_prune_shas=allowed_complete_prune_shas,
        )
        images = prune_failed_images(allowed_failed_shas)
        builder_cache = (
            prune_builder_cache()
            if should_prune_builder_cache(
                retain_complete=args.retain_complete,
                explicitly_requested=args.prune_builder_cache,
            )
            else {"builder_cache_prune": "SKIPPED"}
        )
        report = {
            "record_type": "NUTEV_RELEASE_RECOVERY_HYGIENE",
            "schema_version": 5,
            "status": "PASS",
            **recovery,
            **images,
            **builder_cache,
            "approved_failed_sha_count": len(allowed_failed_shas),
            "protected_sha_count": len(protected_shas),
            "scientific_data_modified": False,
        }
    except (OSError, ValueError, RuntimeError) as exc:
        report = {
            "record_type": "NUTEV_RELEASE_RECOVERY_HYGIENE",
            "schema_version": 5,
            "status": "FAIL",
            "reason": str(exc),
            "scientific_data_modified": False,
        }
    print(json.dumps(report, sort_keys=True, indent=2 if args.json else None))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
