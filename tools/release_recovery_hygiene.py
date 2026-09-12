"""Conservative hygiene for NutEV release-recovery state.

Only canonical recovery directories that are provably incomplete and whose target
SHA belongs to an explicitly approved failed-deploy allowlist are removed.
Complete snapshots, suspicious/corrupt-looking directories, unknown names and
symlinks are preserved for manual review.

The CLI also reclaims Docker image tags only when they are named ``nutev:<SHA>``,
the SHA is in that same failed-deploy allowlist, and no running or stopped
container references the image. A final ordinary ``docker image prune`` removes
only dangling, unused images. Scientific output volumes are never touched.
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


def _validated_allowlist(values: set[str]) -> set[str]:
    if any(not SHA.fullmatch(value) for value in values):
        raise ValueError("failed-deploy allowlist contains an invalid SHA")
    return values


def prune_incomplete(
    base: Path,
    *,
    allowed_failed_shas: set[str],
    exclude: Path | None = None,
) -> dict:
    allowed_failed_shas = _validated_allowlist(set(allowed_failed_shas))
    base.mkdir(parents=True, exist_ok=True)
    if base.is_symlink() or not base.is_dir():
        raise ValueError("recovery base must be a real directory")
    base_resolved = base.resolve()
    excluded = exclude.resolve() if exclude is not None else None
    if excluded is not None and excluded.parent != base_resolved:
        raise ValueError("excluded recovery directory must be inside recovery base")

    pruned = 0
    preserved_complete = 0
    preserved_suspicious = 0
    preserved_unapproved = 0
    skipped_unknown = 0

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
            preserved_complete += 1
            continue
        if state is None:
            preserved_suspicious += 1
            continue
        if target_sha not in allowed_failed_shas:
            preserved_unapproved += 1
            continue

        shutil.rmtree(entry)
        pruned += 1

    return {
        "pruned_incomplete": pruned,
        "preserved_complete": preserved_complete,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--exclude", type=Path)
    parser.add_argument("--allow-sha", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    allowed_failed_shas = set(args.allow_sha)
    try:
        recovery = prune_incomplete(
            args.base,
            allowed_failed_shas=allowed_failed_shas,
            exclude=args.exclude,
        )
        images = prune_failed_images(allowed_failed_shas)
        report = {
            "record_type": "NUTEV_RELEASE_RECOVERY_HYGIENE",
            "schema_version": 3,
            "status": "PASS",
            **recovery,
            **images,
            "approved_failed_sha_count": len(allowed_failed_shas),
            "scientific_data_modified": False,
        }
    except (OSError, ValueError, RuntimeError) as exc:
        report = {
            "record_type": "NUTEV_RELEASE_RECOVERY_HYGIENE",
            "schema_version": 3,
            "status": "FAIL",
            "reason": str(exc),
            "scientific_data_modified": False,
        }
    print(json.dumps(report, sort_keys=True, indent=2 if args.json else None))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
