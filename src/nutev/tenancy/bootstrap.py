from __future__ import annotations

from pathlib import Path
import sqlite3

from .access import _apply_schema as _apply_tenancy_schema
from .applications import _apply_schema as _apply_application_schema
from .auth import _apply_schema as _apply_auth_schema

CORE_PLATFORM_TABLES = frozenset(
    {
        "platform_auth_users",
        "platform_auth_sessions",
        "platform_workspaces",
        "platform_workspace_memberships",
        "platform_projects",
        "platform_session_contexts",
        "platform_research_applications",
    }
)


def initialize_platform_database(database_path: Path) -> tuple[str, ...]:
    """Materialize only the empty core platform schema, idempotently.

    This startup bootstrap deliberately creates no users, workspaces, projects,
    research applications, scientific records, searches, or ownership bindings.
    It exists so a pilot deployment is structurally ready and auditable before
    the first authenticated request reaches the server.
    """

    requested = Path(database_path).expanduser()
    if requested.exists() and requested.is_symlink():
        raise ValueError("platform database path must not be a symlink")
    database = requested.resolve()
    database.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database, timeout=30) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        _apply_auth_schema(connection)
        _apply_tenancy_schema(connection)
        _apply_application_schema(connection)
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    missing = sorted(CORE_PLATFORM_TABLES - tables)
    if missing:
        raise RuntimeError(
            "platform schema bootstrap incomplete: " + ", ".join(missing)
        )
    return tuple(sorted(CORE_PLATFORM_TABLES))
