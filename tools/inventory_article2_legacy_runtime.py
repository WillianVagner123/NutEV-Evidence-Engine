"""Read-only inventory for Article 2 legacy runtime candidates.

This tool produces content fingerprints and safe structural metadata only. It never
classifies a candidate as Article 2, never creates LegacyBindingEvidence, never
mutates scientific state, and never treats a directory/workstream name as ownership.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

RECORD_TYPE = "NUTEV_ARTICLE2_LEGACY_RUNTIME_INVENTORY"
SAFE_METADATA_KEYS = (
    "record_type",
    "schema_version",
    "article_scope",
    "governance_version",
    "governance_digest",
    "config_digest",
    "record_count",
    "total_records",
    "unique_references",
)


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_dirs(roots: list[Path], max_depth: int) -> list[Path]:
    found: dict[str, Path] = {}

    def visit(path: Path, depth: int) -> None:
        if depth > max_depth or path.is_symlink() or not path.is_dir():
            return
        if path.name.startswith("project_output"):
            found[str(path.resolve())] = path.resolve()
            return
        if depth == max_depth:
            return
        try:
            children = sorted(path.iterdir(), key=lambda item: item.name.casefold())
        except OSError:
            return
        for child in children:
            if child.is_dir() and not child.is_symlink():
                visit(child, depth + 1)

    for root in roots:
        visit(root.expanduser().resolve(), 0)
    return [found[key] for key in sorted(found)]


def _safe_json_metadata(path: Path) -> dict[str, Any]:
    name = path.name.casefold()
    if path.suffix.casefold() != ".json" or not (
        "manifest" in name or "audit" in name or name == "latest.json"
    ):
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    safe: dict[str, Any] = {}
    for key in SAFE_METADATA_KEYS:
        value = raw.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
    return safe


def _inventory_candidate(path: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    extension_counts: Counter[str] = Counter()
    metadata: list[dict[str, Any]] = []
    entries: list[tuple[str, int, str]] = []
    symlinks_skipped = 0

    try:
        iterator = sorted(path.rglob("*"), key=lambda item: str(item.relative_to(path)).casefold())
    except OSError as exc:
        return {}, [f"candidate_traversal_failed:{type(exc).__name__}"]

    for item in iterator:
        try:
            if item.is_symlink():
                symlinks_skipped += 1
                continue
            if not item.is_file():
                continue
            relative = item.relative_to(path).as_posix()
            size = item.stat().st_size
            digest = _file_sha256(item)
            relative_digest = _sha256_text(relative)
            entries.append((relative_digest, size, digest))
            extension_counts[item.suffix.casefold() or "<none>"] += 1
            safe = _safe_json_metadata(item)
            if safe:
                metadata.append(
                    {
                        "file_identity_sha256": relative_digest,
                        "file_sha256": digest,
                        "bytes": size,
                        "safe_metadata": safe,
                    }
                )
        except (OSError, ValueError) as exc:
            errors.append(f"file_read_failed:{type(exc).__name__}")

    tree = sha256()
    total_bytes = 0
    for relative_digest, size, digest in entries:
        tree.update(f"{relative_digest}\0{size}\0{digest}\n".encode("ascii"))
        total_bytes += size

    resolved_digest = _sha256_text(str(path.resolve()))
    candidate = {
        "candidate_id": "a2cand_" + resolved_digest[:20],
        "location_fingerprint_sha256": resolved_digest,
        "ownership": "UNKNOWN_UNTIL_REVIEW",
        "classification_inferred": False,
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "tree_sha256": tree.hexdigest(),
        "source_fingerprint": tree.hexdigest(),
        "extension_counts": dict(sorted(extension_counts.items())),
        "safe_manifest_metadata": metadata,
        "symlinks_skipped": symlinks_skipped,
        "raw_path_exposed": False,
        "query_text_exposed": False,
        "search_id_exposed": False,
    }
    return candidate, errors


def build_inventory(roots: list[Path], *, max_depth: int = 2) -> dict[str, Any]:
    candidates = _candidate_dirs(roots, max_depth)
    payload: list[dict[str, Any]] = []
    errors: list[str] = []
    for candidate_path in candidates:
        candidate, candidate_errors = _inventory_candidate(candidate_path)
        if candidate:
            payload.append(candidate)
        errors.extend(candidate_errors)

    manifest_basis = {
        "record_type": RECORD_TYPE,
        "schema_version": 1,
        "candidates": payload,
        "classification_rule": "Candidate names/paths/login/workstream labels do not establish Article 2 ownership.",
    }
    inventory_sha256 = _sha256_text(
        json.dumps(manifest_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    return {
        **manifest_basis,
        "status": "PASS" if not errors else "FAIL",
        "read_only": True,
        "scientific_state_modified": False,
        "legacy_binding_performed": False,
        "search_executed": False,
        "ownership_inferred_from_names": False,
        "candidate_count": len(payload),
        "inventory_sha256": inventory_sha256,
        "errors": errors,
        "binding_status": "NOT_CREATED_REVIEW_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        action="append",
        type=Path,
        required=True,
        help="Read-only root to scan for project_output* candidate directories. Repeatable.",
    )
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.max_depth < 0 or args.max_depth > 6:
        raise SystemExit("--max-depth must be between 0 and 6")
    report = build_inventory(args.root, max_depth=args.max_depth)
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.json else None, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
