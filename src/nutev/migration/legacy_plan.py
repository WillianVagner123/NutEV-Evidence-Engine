from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from fnmatch import fnmatchcase
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable


MIGRATION_MANIFEST_SCHEMA_VERSION = 1


class OwnershipClass(StrEnum):
    GLOBAL = "GLOBAL"
    WILLIAN_PRIVATE = "WILLIAN_PRIVATE"
    ARTICLE1_PRIVATE = "ARTICLE1_PRIVATE"
    ARTICLE2_PRIVATE = "ARTICLE2_PRIVATE"
    SYSTEM = "SYSTEM"
    UNKNOWN = "UNKNOWN"


MIGRATABLE_PRIVATE_CLASSES = {
    OwnershipClass.WILLIAN_PRIVATE,
    OwnershipClass.ARTICLE1_PRIVATE,
    OwnershipClass.ARTICLE2_PRIVATE,
}


@dataclass(frozen=True, slots=True)
class LogicalTarget:
    key: str
    kind: str
    label: str
    parent_key: str | None = None
    application_template: str | None = None

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("target key is required")
        if self.kind not in {"user", "workspace", "project"}:
            raise ValueError("target kind must be user, workspace, or project")
        if not self.label.strip():
            raise ValueError("target label is required")
        if self.kind == "project" and not self.parent_key:
            raise ValueError("project target requires a parent workspace key")
        if self.kind != "project" and self.application_template is not None:
            raise ValueError("only project targets may bind an application template")


@dataclass(frozen=True, slots=True)
class MappingRule:
    pattern: str
    classification: OwnershipClass
    target_key: str | None
    evidence: str
    root_name: str | None = None
    source: str = "profile"

    def __post_init__(self) -> None:
        pattern = self.pattern.strip().replace("\\", "/")
        if not pattern or pattern.startswith("/") or "../" in f"/{pattern}":
            raise ValueError("mapping pattern must be a safe relative path pattern")
        if not self.evidence.strip():
            raise ValueError("mapping rule requires explicit evidence")
        if self.classification in MIGRATABLE_PRIVATE_CLASSES and not self.target_key:
            raise ValueError("private migration classification requires a logical target")
        if self.classification in {
            OwnershipClass.GLOBAL,
            OwnershipClass.SYSTEM,
            OwnershipClass.UNKNOWN,
        } and self.target_key:
            raise ValueError("GLOBAL/SYSTEM/UNKNOWN rules cannot attach a private target")

    def matches(self, root: Path, relative_path: str) -> bool:
        if self.root_name and root.name != self.root_name:
            return False
        return fnmatchcase(relative_path, self.pattern)


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    plan_id: str
    owner_label: str
    targets: tuple[LogicalTarget, ...]
    rules: tuple[MappingRule, ...] = field(default_factory=tuple)
    required_target_keys: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.plan_id.strip():
            raise ValueError("plan_id is required")
        if not self.owner_label.strip():
            raise ValueError("owner_label is required")
        target_keys = [target.key for target in self.targets]
        if len(target_keys) != len(set(target_keys)):
            raise ValueError("logical target keys must be unique")
        known = set(target_keys)
        for target in self.targets:
            if target.parent_key and target.parent_key not in known:
                raise ValueError(f"unknown parent target: {target.parent_key}")
        for rule in self.rules:
            if rule.target_key and rule.target_key not in known:
                raise ValueError(f"mapping rule references unknown target: {rule.target_key}")
        for key in self.required_target_keys:
            if key not in known:
                raise ValueError(f"unknown required target: {key}")


@dataclass(frozen=True, slots=True)
class ExplicitMappingDocument:
    rules: tuple[MappingRule, ...]
    sha256: str
    path: str


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def load_explicit_mapping(path: Path | None) -> ExplicitMappingDocument | None:
    if path is None:
        return None
    mapping_path = Path(path).expanduser().resolve()
    raw = mapping_path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict) or int(payload.get("schema_version") or 0) != 1:
        raise ValueError("explicit mapping requires schema_version=1")
    values = payload.get("rules")
    if not isinstance(values, list):
        raise ValueError("explicit mapping rules must be a list")
    rules: list[MappingRule] = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("each explicit mapping rule must be an object")
        try:
            classification = OwnershipClass(str(item.get("classification") or ""))
        except ValueError as exc:
            raise ValueError("invalid explicit mapping classification") from exc
        rules.append(
            MappingRule(
                pattern=str(item.get("pattern") or ""),
                classification=classification,
                target_key=str(item.get("target_key") or "").strip() or None,
                evidence=str(item.get("evidence") or ""),
                root_name=str(item.get("root_name") or "").strip() or None,
                source="explicit_mapping",
            )
        )
    return ExplicitMappingDocument(
        rules=tuple(rules),
        sha256=sha256(raw).hexdigest(),
        path=str(mapping_path),
    )


def _scan_sources(source_roots: Iterable[Path]) -> tuple[tuple[Path, ...], tuple[dict[str, str], ...]]:
    """Return regular files plus symlink observations without following symlinks."""

    files: list[Path] = []
    symlinks: list[dict[str, str]] = []
    seen_files: set[str] = set()
    seen_links: set[tuple[str, str]] = set()

    for source_root in source_roots:
        root = Path(source_root).expanduser().resolve()
        if not root.is_dir():
            continue
        for candidate in sorted(root.rglob("*")):
            if candidate.is_symlink():
                relative = candidate.relative_to(root).as_posix()
                key = (str(root), relative)
                if key not in seen_links:
                    symlinks.append(
                        {
                            "source_root": str(root),
                            "relative_path": relative,
                            "followed": "false",
                            "migration_action": "NO_AUTOMATIC_MIGRATION",
                        }
                    )
                    seen_links.add(key)
                continue
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if not _inside(resolved, root):
                continue
            key = str(resolved)
            if key not in seen_files:
                files.append(resolved)
                seen_files.add(key)

    return tuple(files), tuple(symlinks)


def _matching_rules(
    root: Path,
    relative_path: str,
    rules: Iterable[MappingRule],
) -> tuple[MappingRule, ...]:
    matched = [rule for rule in rules if rule.matches(root, relative_path)]
    unique: dict[tuple[str, str | None, str], MappingRule] = {}
    for rule in matched:
        unique[(rule.classification.value, rule.target_key, rule.evidence)] = rule
    return tuple(unique.values())


def _classification_for(
    root: Path,
    relative_path: str,
    rules: Iterable[MappingRule],
) -> tuple[OwnershipClass, str | None, str, str, bool]:
    matched = _matching_rules(root, relative_path, rules)
    if not matched:
        return OwnershipClass.UNKNOWN, None, "no_explicit_mapping_rule", "none", False
    semantics = {(rule.classification, rule.target_key) for rule in matched}
    if len(semantics) != 1:
        evidence = " | ".join(sorted(rule.evidence for rule in matched))
        return (
            OwnershipClass.UNKNOWN,
            None,
            f"mapping_conflict: {evidence}",
            "conflict",
            True,
        )
    first = matched[0]
    evidence = " | ".join(sorted({rule.evidence for rule in matched}))
    sources = "+".join(sorted({rule.source for rule in matched}))
    return first.classification, first.target_key, evidence, sources, False


def _target_descriptor(target: LogicalTarget) -> dict[str, object]:
    return {
        "key": target.key,
        "kind": target.kind,
        "label": target.label,
        "parent_key": target.parent_key,
        "application_template": target.application_template,
        "activation_id": None,
        "activation_state": "UNRESOLVED_DRY_RUN",
    }


def run_legacy_multitenant_dry_run(
    *,
    plan: MigrationPlan,
    source_roots: Iterable[Path],
    report_path: Path,
    explicit_mapping_path: Path | None = None,
) -> dict[str, Any]:
    """Plan a reference-only legacy migration without mutating sources or platform state."""

    roots = tuple(
        Path(root).expanduser().resolve()
        for root in source_roots
        if Path(root).expanduser().resolve().is_dir()
    )
    destination = Path(report_path).expanduser().resolve()
    for root in roots:
        if _inside(destination, root):
            raise ValueError("migration report must be outside every legacy source root")

    if explicit_mapping_path is not None:
        mapping_candidate = Path(explicit_mapping_path).expanduser().resolve()
        for root in roots:
            if _inside(mapping_candidate, root):
                raise ValueError("explicit mapping must be outside every legacy source root")

    explicit = load_explicit_mapping(explicit_mapping_path)
    rules = tuple(plan.rules) + (explicit.rules if explicit else ())
    files, symlinks = _scan_sources(roots)
    root_for_file: dict[Path, Path] = {}
    for file_path in files:
        matches = [root for root in roots if _inside(file_path, root)]
        if not matches:
            continue
        root_for_file[file_path] = sorted(
            matches,
            key=lambda item: len(str(item)),
            reverse=True,
        )[0]

    before_hashes = {path: _sha256_file(path) for path in files}
    records: list[dict[str, Any]] = []
    target_counts = {target.key: 0 for target in plan.targets}
    class_counts = {item.value: 0 for item in OwnershipClass}
    mapping_conflicts = 0

    for path in files:
        root = root_for_file[path]
        relative = path.relative_to(root).as_posix()
        classification, target_key, evidence, mapping_source, conflict = _classification_for(
            root,
            relative,
            rules,
        )
        class_counts[classification.value] += 1
        if target_key:
            target_counts[target_key] += 1
        mapping_conflicts += int(conflict)
        stat = path.stat()
        records.append(
            {
                "source_root": str(root),
                "relative_path": relative,
                "size_bytes": int(stat.st_size),
                "source_sha256_before": before_hashes[path],
                "classification": classification.value,
                "logical_target_key": target_key,
                "mapping_evidence": evidence,
                "mapping_source": mapping_source,
                "migration_action": (
                    "REFERENCE_ONLY"
                    if classification in MIGRATABLE_PRIVATE_CLASSES
                    else "NO_AUTOMATIC_MIGRATION"
                ),
            }
        )

    after_hashes = {path: _sha256_file(path) for path in files}
    changed_sources = [
        str(path)
        for path in files
        if before_hashes[path] != after_hashes[path]
    ]
    for record, path in zip(records, files, strict=True):
        record["source_sha256_after"] = after_hashes[path]
        record["source_unchanged"] = before_hashes[path] == after_hashes[path]

    blockers: list[dict[str, str]] = []
    if mapping_conflicts:
        blockers.append(
            {
                "code": "MAPPING_CONFLICT",
                "detail": f"{mapping_conflicts} file(s) matched conflicting ownership rules",
            }
        )
    if changed_sources:
        blockers.append(
            {
                "code": "SOURCE_SHA_MISMATCH",
                "detail": f"{len(changed_sources)} source file(s) changed during dry-run",
            }
        )
    if symlinks:
        blockers.append(
            {
                "code": "SYMLINK_NOT_FOLLOWED",
                "detail": (
                    f"{len(symlinks)} symlink(s) were observed, not followed, and excluded "
                    "from automatic migration"
                ),
            }
        )
    unknown_count = class_counts[OwnershipClass.UNKNOWN.value]
    if unknown_count:
        blockers.append(
            {
                "code": "UNKNOWN_OWNERSHIP_REMAINS",
                "detail": (
                    f"{unknown_count} file(s) remain UNKNOWN and are excluded from automatic migration"
                ),
            }
        )
    for key in plan.required_target_keys:
        if target_counts.get(key, 0) == 0:
            blockers.append(
                {
                    "code": "REQUIRED_TARGET_NOT_MATERIALIZED",
                    "detail": f"No explicitly mapped source files for required target {key}",
                }
            )

    if not roots or (not files and not symlinks):
        status = "SOURCE_NOT_MATERIALIZED"
    elif changed_sources or mapping_conflicts:
        status = "DRY_RUN_FAIL"
    elif blockers:
        status = "DRY_RUN_REVIEW_REQUIRED"
    else:
        status = "DRY_RUN_PASS"

    payload: dict[str, Any] = {
        "schema_version": MIGRATION_MANIFEST_SCHEMA_VERSION,
        "manifest_type": "LEGACY_MULTITENANT_MIGRATION_DRY_RUN",
        "plan_id": plan.plan_id,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": True,
        "activation_supported": False,
        "mutation_policy": {
            "source_files_written": False,
            "platform_database_written": False,
            "searches_executed": False,
            "scientific_results_recomputed": False,
            "human_decisions_changed": False,
            "prisma_recreated": False,
        },
        "owner": {
            "label": plan.owner_label,
            "activation_user_id": None,
            "activation_state": "UNRESOLVED_DRY_RUN",
        },
        "logical_targets": [_target_descriptor(target) for target in plan.targets],
        "source_roots": [str(root) for root in roots],
        "explicit_mapping": (
            {
                "path": explicit.path,
                "sha256": explicit.sha256,
                "rule_count": len(explicit.rules),
            }
            if explicit
            else None
        ),
        "counts": {
            "files_seen": len(records),
            "symlinks_seen": len(symlinks),
            "by_classification": class_counts,
            "by_target": target_counts,
            "mapping_conflicts": mapping_conflicts,
            "source_sha_mismatches": len(changed_sources),
        },
        "blockers": blockers,
        "records": records,
        "symlinks": list(symlinks),
        "guardrails": {
            "unknown_never_auto_migrated": True,
            "symlinks_never_followed_or_auto_migrated": True,
            "migration_by_reference_only": True,
            "control_mapping_outside_source_roots": True,
            "opaque_activation_ids_not_inferred": True,
            "current_login_not_ownership_evidence": True,
            "query_or_search_id_not_ownership_evidence": True,
            "article_identity_not_rewritten": True,
        },
    }
    canonical = _json(payload).encode("utf-8")
    payload["manifest_content_sha256"] = sha256(canonical).hexdigest()

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return payload
