"""Read-only, public-safe audit of Willian doctorate application materialization.

The report never binds ownership, executes searches, changes scientific state or
prints user identities, project names, raw tenant IDs, queries, paths or secrets.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
from urllib.parse import quote

A1 = "WILLIAN_DOCTORATE_A1"
A2 = "WILLIAN_DOCTORATE_A2"
PLATFORM_TABLES = {
    "platform_research_applications",
    "platform_projects",
    "platform_workspaces",
}
SQLITE_SUFFIXES = {".sqlite3", ".sqlite", ".db"}


def _fingerprint(*values: str) -> str:
    return sha256("\x1f".join(values).encode("utf-8")).hexdigest()[:16]


def _file_digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _connect_read_only(database: Path) -> sqlite3.Connection:
    if database.is_symlink() or not database.is_file():
        raise ValueError("runtime database unavailable")
    uri = "file:" + quote(str(database.resolve()), safe="/") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _has_table(connection: sqlite3.Connection, name: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        is not None
    )


def _looks_like_sqlite(path: Path) -> bool:
    if path.is_symlink() or not path.is_file() or path.suffix.casefold() not in SQLITE_SUFFIXES:
        return False
    try:
        with path.open("rb") as stream:
            return stream.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def _is_platform_database(path: Path) -> bool:
    if not _looks_like_sqlite(path):
        return False
    try:
        with _connect_read_only(path) as connection:
            return all(_has_table(connection, name) for name in PLATFORM_TABLES)
    except (OSError, ValueError, sqlite3.Error):
        return False


def _resolve_platform_database(database: Path, output_root: Path) -> tuple[Path, str, int]:
    """Resolve the platform DB without guessing from filenames.

    The configured/default path wins when it exists and has the tenancy/application
    table signature. If it is unavailable, the persistent output tree is scanned
    read-only for SQLite files with that exact signature. Exactly one match is
    required; zero or multiple matches fail closed.
    """

    if _is_platform_database(database):
        return database, "CONFIGURED_OR_DEFAULT_SIGNATURE_MATCH", 1

    candidates: list[Path] = []
    if output_root.is_dir() and not output_root.is_symlink():
        for candidate in sorted(output_root.rglob("*")):
            if _is_platform_database(candidate):
                candidates.append(candidate)

    if not candidates:
        raise ValueError("platform runtime database not materialized")
    if len(candidates) > 1:
        raise ValueError("ambiguous multiple platform runtime databases")
    return candidates[0], "DISCOVERED_SIGNATURE_MATCH", len(candidates)


def audit(database: Path, output_root: Path) -> dict:
    report = {
        "record_type": "NUTEV_WILLIAN_DOCTORATE_RUNTIME_AUDIT",
        "schema_version": 2,
        "status": "PASS",
        "read_only": True,
        "scientific_state_modified": False,
        "legacy_binding_performed": False,
        "search_executed": False,
        "ownership_inferred_from_names": False,
    }
    resolved_database, resolution, candidate_count = _resolve_platform_database(
        database, output_root
    )
    report["platform_database"] = {
        "resolution": resolution,
        "signature_match_count": candidate_count,
        "raw_path_exposed": False,
    }

    with _connect_read_only(resolved_database) as connection:
        missing = sorted(name for name in PLATFORM_TABLES if not _has_table(connection, name))
        if missing:
            raise ValueError("required tenancy/application tables unavailable")
        rows = connection.execute(
            """
            SELECT a.id AS application_id,a.project_id,a.application_type,a.template_id,
                   a.template_version,a.config_version,a.configuration_json,a.status,
                   p.workspace_id
            FROM platform_research_applications a
            JOIN platform_projects p ON p.id=a.project_id
            JOIN platform_workspaces w ON w.id=p.workspace_id
            WHERE a.status='active'
            """
        ).fetchall()
        matches = {A1: [], A2: []}
        for row in rows:
            try:
                configuration = json.loads(str(row["configuration_json"] or "{}"))
            except json.JSONDecodeError:
                configuration = {}
            assembly = (
                str(configuration.get("assembly_id") or "")
                if isinstance(configuration, dict)
                else ""
            )
            if assembly in matches:
                matches[assembly].append(
                    {
                        "application_type": str(row["application_type"]),
                        "template_id": str(row["template_id"] or ""),
                        "template_version": str(row["template_version"] or ""),
                        "config_version": str(row["config_version"]),
                        "scope_fingerprint": _fingerprint(
                            str(row["workspace_id"]),
                            str(row["project_id"]),
                            str(row["application_id"]),
                        ),
                        "_workspace_id": str(row["workspace_id"]),
                        "_project_id": str(row["project_id"]),
                        "_application_id": str(row["application_id"]),
                    }
                )

        a1 = matches[A1]
        pin_workspace = str(os.environ.get("NUTEV_A1_WORKSPACE_ID") or "").strip()
        pin_project = str(os.environ.get("NUTEV_A1_PROJECT_ID") or "").strip()
        if len(a1) == 1:
            pin_state = (
                "OWNER_PINS_MATCH"
                if pin_workspace == a1[0]["_workspace_id"]
                and pin_project == a1[0]["_project_id"]
                else (
                    "OWNER_PINS_MISSING"
                    if not pin_workspace or not pin_project
                    else "OWNER_PINS_MISMATCH"
                )
            )
        elif not a1:
            pin_state = "APPLICATION_NOT_MATERIALIZED"
        else:
            pin_state = "AMBIGUOUS_MULTIPLE_APPLICATIONS"

        manifest = output_root / "agent_context" / "article1" / "CONTEXT_MANIFEST.json"
        report["article1"] = {
            "application_count": len(a1),
            "owner_pin_state": pin_state,
            "application_scopes": [
                {k: v for k, v in item.items() if not k.startswith("_")} for item in a1
            ],
            "agent_context_manifest": {
                "present": manifest.is_file() and not manifest.is_symlink(),
                "sha256": (
                    _file_digest(manifest)
                    if manifest.is_file() and not manifest.is_symlink()
                    else None
                ),
                "bytes": (
                    manifest.stat().st_size
                    if manifest.is_file() and not manifest.is_symlink()
                    else None
                ),
            },
            "formal_search_authorized": False,
        }

        a2 = matches[A2]
        workflows = []
        if len(a2) == 1 and _has_table(connection, "article2_integrative_workflows"):
            for row in connection.execute(
                """
                SELECT workflow_id,current_phase,workflow_status,legacy_binding_state,
                       legacy_binding_fingerprint,config_version
                FROM article2_integrative_workflows
                WHERE workspace_id=? AND project_id=? AND application_id=?
                ORDER BY updated_at DESC
                """,
                (
                    a2[0]["_workspace_id"],
                    a2[0]["_project_id"],
                    a2[0]["_application_id"],
                ),
            ).fetchall():
                workflows.append(
                    {
                        "workflow_fingerprint": _fingerprint(str(row["workflow_id"])),
                        "current_phase": str(row["current_phase"]),
                        "workflow_status": str(row["workflow_status"]),
                        "legacy_binding_state": str(row["legacy_binding_state"]),
                        "legacy_binding_fingerprint_present": bool(
                            row["legacy_binding_fingerprint"]
                        ),
                        "config_version": str(row["config_version"]),
                    }
                )
        report["article2"] = {
            "application_count": len(a2),
            "application_scopes": [
                {k: v for k, v in item.items() if not k.startswith("_")} for item in a2
            ],
            "workflow_count": len(workflows),
            "workflows": workflows,
            "historical_binding_activated": any(
                item["legacy_binding_fingerprint_present"] for item in workflows
            ),
        }

    parent = output_root.resolve().parent
    siblings = []
    if parent.is_dir():
        for item in sorted(parent.glob("project_output*")):
            if item.is_dir() and not item.is_symlink():
                siblings.append(
                    {
                        "kind": "project_output_tree",
                        "ownership": "UNKNOWN_UNTIL_REVIEW",
                    }
                )
    report["legacy_runtime_inventory"] = {
        "candidate_tree_count": len(siblings),
        "candidates": siblings,
        "classification_rule": "No ownership is inferred from directory names.",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=Path(
            os.environ.get("NUTEV_AUTH_DB")
            or "project_output_reference/platform/auth.sqlite3"
        ),
    )
    parser.add_argument(
        "--output-root", type=Path, default=Path("project_output_reference")
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = audit(args.database, args.output_root)
    except (OSError, ValueError, sqlite3.Error) as exc:
        report = {
            "record_type": "NUTEV_WILLIAN_DOCTORATE_RUNTIME_AUDIT",
            "schema_version": 2,
            "status": "FAIL",
            "reason": str(exc),
            "read_only": True,
            "scientific_state_modified": False,
            "legacy_binding_performed": False,
            "search_executed": False,
        }
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2 if args.json else None,
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
