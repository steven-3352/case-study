"""User authentication + session store for the multi-user server.

Zero third-party dependencies: passwords are hashed with ``hashlib.scrypt``
and session tokens are minted with ``secrets``. Backed by a dedicated SQLite
database that lives OUTSIDE any per-user workspace (the global account store),
so it never mixes with a user's own project data.

Design notes
------------
* Registration is gated by a hard-coded invite code (see ``INVITE_CODE``).
  This is deliberately not configurable — it is a short-lived deployment gate.
* User ids are opaque random tokens, used as the per-user workspace directory
  name. They are validated to be filesystem-safe before ever touching disk.
* This module owns NO provider credentials and NO project data. It only knows
  usernames, password hashes, and live session tokens.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from pathlib import Path


class AuthError(Exception):
    """Base class for authentication failures."""


class RegistrationError(AuthError):
    """Registration was rejected (bad invite code, taken username, weak input)."""


class LoginError(AuthError):
    """Credentials did not match a known user."""


# Hard-coded registration gate. Short-lived deployment; intentionally not a
# config value or env var so it cannot leak into per-user settings files.
INVITE_CODE = "jenny"

# scrypt work factors. n must be a power of two; these are the standard
# interactive-login parameters (~16 MiB memory per hash).
_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_SESSION_TTL_SECONDS = 30 * 24 * 3600  # 30 days


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt,
        n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_DKLEN,
    )


class AuthStore:
    """SQLite-backed user + session store. One instance per process.

    Every method opens its own short-lived connection (WAL mode, busy_timeout)
    so it is safe to call from FastAPI's threadpool under concurrent requests.
    """

    def __init__(self, db_path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def _connect(self):
        con = sqlite3.connect(str(self.path), isolation_level=None, timeout=5.0)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=5000")
        con.row_factory = sqlite3.Row
        return con

    def _migrate(self):
        with self._connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                  user_id    TEXT PRIMARY KEY,
                  username   TEXT NOT NULL UNIQUE,
                  pw_hash    BLOB NOT NULL,
                  pw_salt    BLOB NOT NULL,
                  created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                  token      TEXT PRIMARY KEY,
                  user_id    TEXT NOT NULL,
                  created_at REAL NOT NULL,
                  expires_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
                """
            )

    # ---- registration & login -------------------------------------------

    def register(self, username, password, invite_code):
        """Create a new user. Returns the new user_id.

        Raises RegistrationError on bad invite code, invalid username/password,
        or a username that is already taken.
        """
        if not hmac.compare_digest(str(invite_code or ""), INVITE_CODE):
            raise RegistrationError("邀请码无效")
        username = (username or "").strip()
        if not _USERNAME_RE.match(username):
            raise RegistrationError("用户名只能含字母/数字/._-,长度 1-64")
        if not isinstance(password, str) or len(password) < 6:
            raise RegistrationError("密码至少 6 位")
        if len(password.encode("utf-8")) > 1024:
            raise RegistrationError("密码过长")
        salt = secrets.token_bytes(16)
        pw_hash = _hash_password(password, salt)
        user_id = "u-" + secrets.token_hex(16)
        try:
            with self._connect() as con:
                con.execute(
                    "INSERT INTO users(user_id, username, pw_hash, pw_salt, created_at)"
                    " VALUES (?,?,?,?,?)",
                    (user_id, username, pw_hash, salt, time.time()),
                )
        except sqlite3.IntegrityError as exc:
            raise RegistrationError("用户名已被占用") from exc
        return user_id

    def authenticate(self, username, password):
        """Verify credentials. Returns user_id on success, else raises LoginError."""
        username = (username or "").strip()
        with self._connect() as con:
            row = con.execute(
                "SELECT user_id, pw_hash, pw_salt FROM users WHERE username=?",
                (username,),
            ).fetchone()
        if row is None:
            # Hash anyway to keep timing roughly constant against user enumeration.
            _hash_password(password or "", b"\x00" * 16)
            raise LoginError("用户名或密码错误")
        expected = bytes(row["pw_hash"])
        actual = _hash_password(password or "", bytes(row["pw_salt"]))
        if not hmac.compare_digest(expected, actual):
            raise LoginError("用户名或密码错误")
        return row["user_id"]

    # ---- sessions --------------------------------------------------------

    def create_session(self, user_id):
        """Mint an opaque session token for user_id. Returns the token string."""
        token = secrets.token_urlsafe(32)
        now = time.time()
        with self._connect() as con:
            con.execute(
                "INSERT INTO sessions(token, user_id, created_at, expires_at)"
                " VALUES (?,?,?,?)",
                (token, user_id, now, now + _SESSION_TTL_SECONDS),
            )
        return token

    def verify_session(self, token):
        """Return the user_id for a live session token, or None if missing/expired."""
        if not token:
            return None
        now = time.time()
        with self._connect() as con:
            row = con.execute(
                "SELECT user_id, expires_at FROM sessions WHERE token=?",
                (token,),
            ).fetchone()
            if row is None:
                return None
            if float(row["expires_at"]) < now:
                con.execute("DELETE FROM sessions WHERE token=?", (token,))
                return None
        return row["user_id"]

    def revoke_session(self, token):
        """Delete a session token (logout). Idempotent."""
        if not token:
            return
        with self._connect() as con:
            con.execute("DELETE FROM sessions WHERE token=?", (token,))

    def get_username(self, user_id):
        """Return the username for a user_id, or None if not found."""
        if not user_id:
            return None
        with self._connect() as con:
            row = con.execute(
                "SELECT username FROM users WHERE user_id=?",
                (user_id,),
            ).fetchone()
        return row["username"] if row else None

    def purge_expired_sessions(self):
        """Best-effort cleanup of expired sessions."""
        with self._connect() as con:
            con.execute("DELETE FROM sessions WHERE expires_at < ?", (time.time(),))
