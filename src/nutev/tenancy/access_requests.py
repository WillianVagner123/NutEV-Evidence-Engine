from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import re
import secrets
import sqlite3

from .auth import SQLiteAuthProvider

ACCESS_REQUEST_TOKEN_TTL_SECONDS = 72 * 60 * 60
_ACCESS_REQUEST_ID_RE = re.compile(r"^acr_[a-f0-9]{32}$")
_ALLOWED_STATUSES = frozenset({"pending", "approved", "rejected", "accepted"})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_email(value: str) -> str:
    email = str(value or "").strip().casefold()
    if not email or "@" not in email or len(email) > 320:
        raise ValueError("invalid email")
    return email


def _required_text(value: str, *, field: str, minimum: int, maximum: int) -> str:
    text = " ".join(str(value or "").strip().split())
    if len(text) < minimum:
        raise ValueError(f"{field} is required")
    if len(text) > maximum:
        raise ValueError(f"{field} is too long")
    return text


def _token_digest(token: str) -> str:
    return sha256(str(token or "").encode("utf-8")).hexdigest()


def _require_request_id(value: str) -> str:
    request_id = str(value or "").strip()
    if not _ACCESS_REQUEST_ID_RE.fullmatch(request_id):
        raise ValueError("invalid access request id")
    return request_id


def _apply_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS platform_access_requests (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL COLLATE NOCASE,
            display_name TEXT NOT NULL,
            institution TEXT NOT NULL,
            intended_use TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            decided_at TEXT,
            decided_by TEXT,
            rejection_reason TEXT,
            invitation_token_hash TEXT UNIQUE,
            invitation_expires_at TEXT,
            accepted_at TEXT,
            accepted_user_id TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_platform_access_requests_status_created
            ON platform_access_requests(status, created_at DESC);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_access_requests_open_email
            ON platform_access_requests(email COLLATE NOCASE)
            WHERE status IN ('pending', 'approved');
        """
    )
    connection.commit()


@dataclass(frozen=True, slots=True)
class AccessRequestRecord:
    id: str
    email: str
    display_name: str
    institution: str
    intended_use: str
    status: str
    created_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None
    rejection_reason: str | None = None
    invitation_expires_at: datetime | None = None
    accepted_at: datetime | None = None
    accepted_user_id: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AccessRequestRecord":
        status = str(row["status"])
        if status not in _ALLOWED_STATUSES:
            raise RuntimeError("unknown access request status")
        return cls(
            id=str(row["id"]),
            email=str(row["email"]),
            display_name=str(row["display_name"]),
            institution=str(row["institution"]),
            intended_use=str(row["intended_use"]),
            status=status,
            created_at=_parse_datetime(str(row["created_at"])) or _now(),
            decided_at=_parse_datetime(row["decided_at"]),
            decided_by=str(row["decided_by"]) if row["decided_by"] else None,
            rejection_reason=str(row["rejection_reason"]) if row["rejection_reason"] else None,
            invitation_expires_at=_parse_datetime(row["invitation_expires_at"]),
            accepted_at=_parse_datetime(row["accepted_at"]),
            accepted_user_id=str(row["accepted_user_id"]) if row["accepted_user_id"] else None,
        )

    def admin_payload(self, *, now: datetime | None = None) -> dict[str, object]:
        current = now or _now()
        expired = bool(
            self.status == "approved"
            and self.invitation_expires_at is not None
            and self.invitation_expires_at <= current
        )
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "institution": self.institution,
            "intended_use": self.intended_use,
            "status": self.status,
            "created_at": _iso(self.created_at),
            "decided_at": _iso(self.decided_at) if self.decided_at else None,
            "decided_by": self.decided_by,
            "rejection_reason": self.rejection_reason,
            "invitation_expires_at": _iso(self.invitation_expires_at) if self.invitation_expires_at else None,
            "invitation_expired": expired,
            "accepted_at": _iso(self.accepted_at) if self.accepted_at else None,
            "accepted_user_id": self.accepted_user_id,
        }


@dataclass(frozen=True, slots=True)
class AccessInvitation:
    request: AccessRequestRecord
    token: str


class SQLiteAccessRequestStore:
    """Governed public access requests and one-time account invitations.

    Raw invitation tokens are returned only when issued. Persistence contains only
    SHA-256 token digests, mirroring the session-token storage boundary.
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path).resolve()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        _apply_schema(connection)
        return connection

    @staticmethod
    def _user_table_exists(connection: sqlite3.Connection) -> bool:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='platform_auth_users'"
        ).fetchone()
        return row is not None

    @classmethod
    def _user_exists(cls, connection: sqlite3.Connection, email: str) -> bool:
        if not cls._user_table_exists(connection):
            return False
        row = connection.execute(
            "SELECT 1 FROM platform_auth_users WHERE email = ? COLLATE NOCASE LIMIT 1",
            (email,),
        ).fetchone()
        return row is not None

    def submit(
        self,
        *,
        email: str,
        display_name: str,
        institution: str,
        intended_use: str,
    ) -> AccessRequestRecord | None:
        canonical_email = _normalize_email(email)
        name = _required_text(display_name, field="display_name", minimum=2, maximum=120)
        organization = _required_text(institution, field="institution", minimum=2, maximum=160)
        purpose = _required_text(intended_use, field="intended_use", minimum=10, maximum=1200)
        created_at = _now()
        request_id = f"acr_{secrets.token_hex(16)}"

        with self._connect() as connection:
            if self._user_exists(connection, canonical_email):
                return None
            existing = connection.execute(
                """
                SELECT * FROM platform_access_requests
                WHERE email = ? COLLATE NOCASE AND status IN ('pending','approved')
                ORDER BY created_at DESC LIMIT 1
                """,
                (canonical_email,),
            ).fetchone()
            if existing is not None:
                return None
            try:
                connection.execute(
                    """
                    INSERT INTO platform_access_requests(
                        id, email, display_name, institution, intended_use, status, created_at
                    ) VALUES(?,?,?,?,?,'pending',?)
                    """,
                    (request_id, canonical_email, name, organization, purpose, _iso(created_at)),
                )
                connection.commit()
            except sqlite3.IntegrityError:
                return None
            row = connection.execute(
                "SELECT * FROM platform_access_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            raise RuntimeError("access request disappeared after creation")
        return AccessRequestRecord.from_row(row)

    def list(self, *, status: str = "pending", limit: int = 200) -> list[AccessRequestRecord]:
        normalized = str(status or "pending").strip().casefold()
        if normalized != "all" and normalized not in _ALLOWED_STATUSES:
            raise ValueError("invalid access request status")
        bounded_limit = max(1, min(int(limit), 500))
        with self._connect() as connection:
            if normalized == "all":
                rows = connection.execute(
                    "SELECT * FROM platform_access_requests ORDER BY created_at DESC LIMIT ?",
                    (bounded_limit,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM platform_access_requests WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (normalized, bounded_limit),
                ).fetchall()
        return [AccessRequestRecord.from_row(row) for row in rows]

    def approve(
        self,
        request_id: str,
        *,
        decided_by: str,
        ttl_seconds: int = ACCESS_REQUEST_TOKEN_TTL_SECONDS,
    ) -> AccessInvitation:
        rid = _require_request_id(request_id)
        actor = _required_text(decided_by, field="decided_by", minimum=4, maximum=128)
        ttl = int(ttl_seconds)
        if ttl < 15 * 60 or ttl > 30 * 24 * 60 * 60:
            raise ValueError("invitation TTL outside allowed range")
        token = secrets.token_urlsafe(32)
        decided_at = _now()
        expires_at = decided_at + timedelta(seconds=ttl)

        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_access_requests WHERE id = ?",
                (rid,),
            ).fetchone()
            if row is None:
                raise KeyError(rid)
            status = str(row["status"])
            if status not in {"pending", "approved"}:
                raise ValueError("access request is not approvable")
            email = str(row["email"])
            if self._user_exists(connection, email):
                raise ValueError("email already has an account")
            connection.execute(
                """
                UPDATE platform_access_requests
                SET status='approved', decided_at=?, decided_by=?, rejection_reason=NULL,
                    invitation_token_hash=?, invitation_expires_at=?
                WHERE id=?
                """,
                (_iso(decided_at), actor, _token_digest(token), _iso(expires_at), rid),
            )
            connection.commit()
            refreshed = connection.execute(
                "SELECT * FROM platform_access_requests WHERE id = ?",
                (rid,),
            ).fetchone()
        if refreshed is None:
            raise RuntimeError("access request disappeared after approval")
        return AccessInvitation(request=AccessRequestRecord.from_row(refreshed), token=token)

    def reject(self, request_id: str, *, decided_by: str, reason: str = "") -> AccessRequestRecord:
        rid = _require_request_id(request_id)
        actor = _required_text(decided_by, field="decided_by", minimum=4, maximum=128)
        rejection = " ".join(str(reason or "").strip().split())
        if len(rejection) > 500:
            raise ValueError("rejection reason is too long")
        decided_at = _now()

        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_access_requests WHERE id = ?",
                (rid,),
            ).fetchone()
            if row is None:
                raise KeyError(rid)
            if str(row["status"]) not in {"pending", "approved"}:
                raise ValueError("access request is not rejectable")
            connection.execute(
                """
                UPDATE platform_access_requests
                SET status='rejected', decided_at=?, decided_by=?, rejection_reason=?,
                    invitation_token_hash=NULL, invitation_expires_at=NULL
                WHERE id=?
                """,
                (_iso(decided_at), actor, rejection or None, rid),
            )
            connection.commit()
            refreshed = connection.execute(
                "SELECT * FROM platform_access_requests WHERE id = ?",
                (rid,),
            ).fetchone()
        if refreshed is None:
            raise RuntimeError("access request disappeared after rejection")
        return AccessRequestRecord.from_row(refreshed)

    def inspect_invitation(self, token: str) -> AccessRequestRecord | None:
        raw = str(token or "").strip()
        if len(raw) < 32 or len(raw) > 256:
            return None
        digest = _token_digest(raw)
        now = _now()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM platform_access_requests
                WHERE invitation_token_hash = ? AND status = 'approved'
                LIMIT 1
                """,
                (digest,),
            ).fetchone()
        if row is None:
            return None
        record = AccessRequestRecord.from_row(row)
        if record.invitation_expires_at is None or record.invitation_expires_at <= now:
            return None
        return record

    def accept_invitation(self, token: str, *, password: str):
        raw = str(token or "").strip()
        record = self.inspect_invitation(raw)
        if record is None:
            raise KeyError("invalid_or_expired_invitation")

        provider = SQLiteAuthProvider(self.database_path)
        user = provider.provision_user(
            email=record.email,
            display_name=record.display_name,
            password=password,
        )
        accepted_at = _now()
        digest = _token_digest(raw)
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE platform_access_requests
                    SET status='accepted', accepted_at=?, accepted_user_id=?,
                        invitation_token_hash=NULL, invitation_expires_at=NULL
                    WHERE id=? AND status='approved' AND invitation_token_hash=?
                    """,
                    (_iso(accepted_at), user.id, record.id, digest),
                )
                connection.commit()
                if cursor.rowcount != 1:
                    raise RuntimeError("invitation changed during account creation")
        except Exception:
            provider.set_user_status(user.id, "disabled")
            raise
        return user
