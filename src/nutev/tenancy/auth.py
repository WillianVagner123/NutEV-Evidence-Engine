from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import secrets
import sqlite3
from typing import Protocol

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from .models import (
    GlobalRole,
    Membership,
    Principal,
    User,
    new_opaque_id,
    require_opaque_id,
)

AUTH_SCHEMA_VERSION = 1
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 1024
DEFAULT_SESSION_TTL_SECONDS = 8 * 60 * 60
MAX_SESSION_TTL_SECONDS = 30 * 24 * 60 * 60


class AuthDataError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_email(value: str) -> str:
    email = str(value or "").strip().casefold()
    if not email or "@" not in email or len(email) > 320:
        raise ValueError("invalid email")
    return email


def _validate_password(value: str) -> str:
    password = str(value or "")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must have at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError("password is too long")
    return password


def _token_digest(token: str) -> str:
    return sha256(str(token or "").encode("utf-8")).hexdigest()


def _apply_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS platform_auth_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS platform_auth_users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            global_roles_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            last_login_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_platform_auth_users_status
            ON platform_auth_users(status);

        CREATE TABLE IF NOT EXISTS platform_auth_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES platform_auth_users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT,
            last_seen_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_platform_auth_sessions_user
            ON platform_auth_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_platform_auth_sessions_expiry
            ON platform_auth_sessions(expires_at);
        """
    )
    connection.execute(
        "INSERT INTO platform_auth_meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(AUTH_SCHEMA_VERSION),),
    )
    connection.commit()


@dataclass(frozen=True, slots=True)
class AuthenticatedSubject:
    user: User
    global_roles: frozenset[GlobalRole]


class AuthProvider(Protocol):
    def authenticate(self, email: str, password: str) -> AuthenticatedSubject | None: ...

    def load_subject(self, user_id: str) -> AuthenticatedSubject | None: ...


class SQLiteAuthProvider:
    """Local identity adapter using Argon2 for password verification.

    The adapter exists so the scientific engine is not coupled to a particular identity
    provider. A future external IdP can implement ``AuthProvider`` without changing the
    Principal/Permission contracts.
    """

    def __init__(self, database_path: Path, *, password_hasher: PasswordHasher | None = None) -> None:
        self.database_path = Path(database_path).resolve()
        self._hasher = password_hasher or PasswordHasher()
        # Used only to reduce obvious user-enumeration timing differences. It is not a credential.
        self._dummy_hash = self._hasher.hash("nutev-auth-timing-equalizer-not-a-user-password")

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        _apply_schema(connection)
        return connection

    @staticmethod
    def _roles(value: str) -> frozenset[GlobalRole]:
        try:
            raw = json.loads(value or "[]")
        except json.JSONDecodeError as exc:
            raise AuthDataError("invalid global role payload") from exc
        if not isinstance(raw, list):
            raise AuthDataError("invalid global role payload")
        roles: set[GlobalRole] = set()
        for item in raw:
            try:
                roles.add(GlobalRole(str(item)))
            except ValueError as exc:
                raise AuthDataError("unknown global role in auth store") from exc
        return frozenset(roles)

    @classmethod
    def _subject_from_row(cls, row: sqlite3.Row) -> AuthenticatedSubject:
        last_login = _parse_datetime(str(row["last_login_at"])) if row["last_login_at"] else None
        user = User(
            id=str(row["id"]),
            email=str(row["email"]),
            display_name=str(row["display_name"]),
            status=str(row["status"]),
            created_at=_parse_datetime(str(row["created_at"])),
            last_login_at=last_login,
        )
        return AuthenticatedSubject(user=user, global_roles=cls._roles(str(row["global_roles_json"])))

    def provision_user(
        self,
        *,
        email: str,
        display_name: str,
        password: str,
        global_roles: Iterable[GlobalRole] = (),
        user_id: str | None = None,
    ) -> User:
        canonical_email = _normalize_email(email)
        display = str(display_name or "").strip()
        if not display:
            raise ValueError("display_name is required")
        secret = _validate_password(password)
        uid = user_id or new_opaque_id("user")
        require_opaque_id(uid, "user")
        roles = frozenset(global_roles)
        encoded_roles = json.dumps(sorted(role.value for role in roles), separators=(",", ":"))
        password_hash = self._hasher.hash(secret)
        created_at = _now()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO platform_auth_users(
                        id, email, display_name, password_hash, status,
                        global_roles_json, created_at, last_login_at
                    ) VALUES(?,?,?,?,?,?,?,NULL)
                    """,
                    (
                        uid,
                        canonical_email,
                        display,
                        password_hash,
                        "active",
                        encoded_roles,
                        _iso(created_at),
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("user already exists") from exc
        return User(
            id=uid,
            email=canonical_email,
            display_name=display,
            status="active",
            created_at=created_at,
        )

    def authenticate(self, email: str, password: str) -> AuthenticatedSubject | None:
        try:
            canonical_email = _normalize_email(email)
        except ValueError:
            canonical_email = ""
        candidate_password = str(password or "")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_auth_users WHERE email = ? COLLATE NOCASE",
                (canonical_email,),
            ).fetchone()
            stored_hash = str(row["password_hash"]) if row is not None else self._dummy_hash
            try:
                verified = self._hasher.verify(stored_hash, candidate_password)
            except (VerifyMismatchError, VerificationError):
                verified = False
            if row is None or not verified or str(row["status"]) != "active":
                return None

            if self._hasher.check_needs_rehash(stored_hash):
                connection.execute(
                    "UPDATE platform_auth_users SET password_hash = ? WHERE id = ?",
                    (self._hasher.hash(candidate_password), str(row["id"])),
                )
            now = _now()
            connection.execute(
                "UPDATE platform_auth_users SET last_login_at = ? WHERE id = ?",
                (_iso(now), str(row["id"])),
            )
            connection.commit()
            refreshed = connection.execute(
                "SELECT * FROM platform_auth_users WHERE id = ?",
                (str(row["id"]),),
            ).fetchone()
            if refreshed is None:
                raise AuthDataError("authenticated user disappeared")
            return self._subject_from_row(refreshed)

    def load_subject(self, user_id: str) -> AuthenticatedSubject | None:
        try:
            require_opaque_id(user_id, "user")
        except ValueError:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_auth_users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None or str(row["status"]) != "active":
            return None
        return self._subject_from_row(row)

    def set_user_status(self, user_id: str, status: str) -> None:
        require_opaque_id(user_id, "user")
        normalized = str(status or "").strip().casefold()
        if normalized not in {"active", "suspended", "disabled"}:
            raise ValueError("invalid user status")
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE platform_auth_users SET status = ? WHERE id = ?",
                (normalized, user_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(user_id)
            connection.commit()


@dataclass(frozen=True, slots=True)
class IssuedSession:
    session_id: str
    user_id: str
    session_token: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class SessionRecord:
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime


class SQLiteSessionStore:
    """Opaque cookie sessions. Only SHA-256(token) is persisted; raw tokens never are."""

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

    def issue(self, user_id: str, *, ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS) -> IssuedSession:
        require_opaque_id(user_id, "user")
        ttl = int(ttl_seconds)
        if ttl < 60 or ttl > MAX_SESSION_TTL_SECONDS:
            raise ValueError("session TTL outside allowed range")
        created_at = _now()
        expires_at = created_at + timedelta(seconds=ttl)
        session_id = new_opaque_id("session")
        raw_token = secrets.token_urlsafe(32)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO platform_auth_sessions(
                    session_id, user_id, token_hash, created_at,
                    expires_at, revoked_at, last_seen_at
                ) VALUES(?,?,?,?,?,NULL,?)
                """,
                (
                    session_id,
                    user_id,
                    _token_digest(raw_token),
                    _iso(created_at),
                    _iso(expires_at),
                    _iso(created_at),
                ),
            )
            connection.commit()
        return IssuedSession(
            session_id=session_id,
            user_id=user_id,
            session_token=raw_token,
            created_at=created_at,
            expires_at=expires_at,
        )

    def resolve(self, session_token: str) -> SessionRecord | None:
        token = str(session_token or "")
        if len(token) < 32 or len(token) > 256:
            return None
        now = _now()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM platform_auth_sessions WHERE token_hash = ?",
                (_token_digest(token),),
            ).fetchone()
            if row is None or row["revoked_at"] is not None:
                return None
            expires_at = _parse_datetime(str(row["expires_at"]))
            if expires_at <= now:
                return None
            connection.execute(
                "UPDATE platform_auth_sessions SET last_seen_at = ? WHERE session_id = ?",
                (_iso(now), str(row["session_id"])),
            )
            connection.commit()
            return SessionRecord(
                session_id=str(row["session_id"]),
                user_id=str(row["user_id"]),
                created_at=_parse_datetime(str(row["created_at"])),
                expires_at=expires_at,
                last_seen_at=now,
            )

    def revoke(self, session_token: str) -> bool:
        token = str(session_token or "")
        if not token:
            return False
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE platform_auth_sessions
                SET revoked_at = COALESCE(revoked_at, ?)
                WHERE token_hash = ?
                """,
                (_iso(_now()), _token_digest(token)),
            )
            connection.commit()
            return cursor.rowcount == 1

    def revoke_all_for_user(self, user_id: str) -> int:
        require_opaque_id(user_id, "user")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE platform_auth_sessions
                SET revoked_at = COALESCE(revoked_at, ?)
                WHERE user_id = ? AND revoked_at IS NULL
                """,
                (_iso(_now()), user_id),
            )
            connection.commit()
            return int(cursor.rowcount)

    def prune(self) -> int:
        now = _iso(_now())
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM platform_auth_sessions WHERE expires_at <= ? OR revoked_at IS NOT NULL",
                (now,),
            )
            connection.commit()
            return int(cursor.rowcount)


MembershipLoader = Callable[[str], Iterable[Membership]]


@dataclass(frozen=True, slots=True)
class SessionPrincipal:
    user: User
    principal: Principal
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class LoginResult:
    session_token: str
    session: SessionPrincipal


class SessionPrincipalService:
    def __init__(
        self,
        auth_provider: AuthProvider,
        session_store: SQLiteSessionStore,
        *,
        membership_loader: MembershipLoader | None = None,
        session_ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ) -> None:
        self.auth_provider = auth_provider
        self.session_store = session_store
        self.membership_loader = membership_loader or (lambda _user_id: ())
        self.session_ttl_seconds = int(session_ttl_seconds)

    def _principal(self, subject: AuthenticatedSubject, session_id: str) -> Principal:
        memberships = tuple(self.membership_loader(subject.user.id))
        return Principal(
            user_id=subject.user.id,
            workspace_memberships=memberships,
            global_roles=subject.global_roles,
            session_id=session_id,
        )

    def login(self, email: str, password: str) -> LoginResult | None:
        subject = self.auth_provider.authenticate(email, password)
        if subject is None:
            return None
        issued = self.session_store.issue(
            subject.user.id,
            ttl_seconds=self.session_ttl_seconds,
        )
        principal = self._principal(subject, issued.session_id)
        return LoginResult(
            session_token=issued.session_token,
            session=SessionPrincipal(
                user=subject.user,
                principal=principal,
                expires_at=issued.expires_at,
            ),
        )

    def resolve(self, session_token: str) -> SessionPrincipal | None:
        record = self.session_store.resolve(session_token)
        if record is None:
            return None
        subject = self.auth_provider.load_subject(record.user_id)
        if subject is None:
            self.session_store.revoke(session_token)
            return None
        principal = self._principal(subject, record.session_id)
        return SessionPrincipal(
            user=subject.user,
            principal=principal,
            expires_at=record.expires_at,
        )

    def logout(self, session_token: str) -> bool:
        return self.session_store.revoke(session_token)
