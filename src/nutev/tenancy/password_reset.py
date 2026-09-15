from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import secrets
import sqlite3

from argon2 import PasswordHasher

from .auth import (
    _apply_schema as _apply_auth_schema,
    _iso,
    _normalize_email,
    _now,
    _parse_datetime,
    _token_digest,
    _validate_password,
)
from .models import User

PASSWORD_RESET_TOKEN_TTL_SECONDS = 60 * 60


def _apply_schema(connection: sqlite3.Connection) -> None:
    _apply_auth_schema(connection)
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS platform_auth_password_resets (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES platform_auth_users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_platform_auth_password_resets_user
            ON platform_auth_password_resets(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_platform_auth_password_resets_expiry
            ON platform_auth_password_resets(expires_at);
        """
    )
    connection.commit()


@dataclass(frozen=True, slots=True)
class PasswordResetRecord:
    id: str
    user_id: str
    email: str
    display_name: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PasswordResetTicket:
    reset: PasswordResetRecord
    token: str


class SQLitePasswordResetStore:
    """One-time password recovery tickets backed by the platform auth database."""

    def __init__(self, database_path: Path, *, password_hasher: PasswordHasher | None = None) -> None:
        self.database_path = Path(database_path).resolve()
        self._hasher = password_hasher or PasswordHasher()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        _apply_schema(connection)
        return connection

    @staticmethod
    def _record(row: sqlite3.Row) -> PasswordResetRecord:
        return PasswordResetRecord(
            id=str(row["reset_id"]),
            user_id=str(row["user_id"]),
            email=str(row["email"]),
            display_name=str(row["display_name"]),
            created_at=_parse_datetime(str(row["created_at"])),
            expires_at=_parse_datetime(str(row["expires_at"])),
            used_at=_parse_datetime(str(row["used_at"])) if row["used_at"] else None,
        )

    def issue(self, email: str, *, ttl_seconds: int = PASSWORD_RESET_TOKEN_TTL_SECONDS) -> PasswordResetTicket | None:
        try:
            canonical_email = _normalize_email(email)
        except ValueError:
            return None
        ttl = int(ttl_seconds)
        if ttl < 15 * 60 or ttl > 24 * 60 * 60:
            raise ValueError("password reset TTL outside allowed range")
        created_at = _now()
        expires_at = created_at + timedelta(seconds=ttl)
        reset_id = f"pwd_{secrets.token_hex(16)}"
        token = secrets.token_urlsafe(32)
        with self._connect() as connection:
            user = connection.execute(
                "SELECT id, email, display_name FROM platform_auth_users WHERE email = ? COLLATE NOCASE AND status = 'active' LIMIT 1",
                (canonical_email,),
            ).fetchone()
            if user is None:
                return None
            connection.execute(
                "UPDATE platform_auth_password_resets SET used_at = COALESCE(used_at, ?) WHERE user_id = ? AND used_at IS NULL",
                (_iso(created_at), str(user["id"])),
            )
            connection.execute(
                "INSERT INTO platform_auth_password_resets(id, user_id, token_hash, created_at, expires_at, used_at) VALUES(?,?,?,?,?,NULL)",
                (reset_id, str(user["id"]), _token_digest(token), _iso(created_at), _iso(expires_at)),
            )
            connection.commit()
        return PasswordResetTicket(
            reset=PasswordResetRecord(
                id=reset_id,
                user_id=str(user["id"]),
                email=str(user["email"]),
                display_name=str(user["display_name"]),
                created_at=created_at,
                expires_at=expires_at,
            ),
            token=token,
        )

    def inspect(self, token: str) -> PasswordResetRecord | None:
        raw = str(token or "").strip()
        if len(raw) < 32 or len(raw) > 256:
            return None
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT r.id AS reset_id, r.user_id, r.created_at, r.expires_at, r.used_at, u.email, u.display_name
                FROM platform_auth_password_resets AS r
                JOIN platform_auth_users AS u ON u.id = r.user_id
                WHERE r.token_hash = ? AND r.used_at IS NULL AND u.status = 'active'
                LIMIT 1
                """,
                (_token_digest(raw),),
            ).fetchone()
        if row is None:
            return None
        record = self._record(row)
        return record if record.expires_at > _now() else None

    def consume(self, token: str, *, password: str) -> User:
        raw = str(token or "").strip()
        if len(raw) < 32 or len(raw) > 256:
            raise KeyError("invalid_or_expired_password_reset")
        secret = _validate_password(password)
        digest = _token_digest(raw)
        used_at = _now()
        password_hash = self._hasher.hash(secret)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT r.id AS reset_id, r.user_id, r.expires_at, u.email, u.display_name,
                       u.created_at AS user_created_at, u.last_login_at, u.status
                FROM platform_auth_password_resets AS r
                JOIN platform_auth_users AS u ON u.id = r.user_id
                WHERE r.token_hash = ? AND r.used_at IS NULL
                LIMIT 1
                """,
                (digest,),
            ).fetchone()
            if row is None or str(row["status"]) != "active" or _parse_datetime(str(row["expires_at"])) <= used_at:
                connection.rollback()
                raise KeyError("invalid_or_expired_password_reset")
            cursor = connection.execute(
                "UPDATE platform_auth_password_resets SET used_at = ? WHERE id = ? AND token_hash = ? AND used_at IS NULL",
                (_iso(used_at), str(row["reset_id"]), digest),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                raise KeyError("invalid_or_expired_password_reset")
            connection.execute("UPDATE platform_auth_users SET password_hash = ? WHERE id = ?", (password_hash, str(row["user_id"])))
            connection.execute(
                "UPDATE platform_auth_sessions SET revoked_at = COALESCE(revoked_at, ?) WHERE user_id = ? AND revoked_at IS NULL",
                (_iso(used_at), str(row["user_id"])),
            )
            connection.execute(
                "UPDATE platform_auth_password_resets SET used_at = COALESCE(used_at, ?) WHERE user_id = ? AND used_at IS NULL",
                (_iso(used_at), str(row["user_id"])),
            )
            connection.commit()
        return User(
            id=str(row["user_id"]),
            email=str(row["email"]),
            display_name=str(row["display_name"]),
            status="active",
            created_at=_parse_datetime(str(row["user_created_at"])),
            last_login_at=_parse_datetime(str(row["last_login_at"])) if row["last_login_at"] else None,
        )
