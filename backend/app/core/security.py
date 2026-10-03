"""Password hashing, JWT issuing/validation, and refresh-token helpers."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.errors import UnauthorizedError

# argon2 by default - `recommended()` picks the strongest sane preset.
_password_hash = PasswordHash.recommended()

ACCESS_TOKEN_TYPE = "access"


# ---------------------------------------------------------------------------
# passwords
# ---------------------------------------------------------------------------
def hash_password(raw_password: str) -> str:
    return _password_hash.hash(raw_password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
    try:
        return _password_hash.verify(raw_password, hashed_password)
    except Exception:
        # Malformed/legacy hashes should read as "wrong password", not a 500.
        return False


# ---------------------------------------------------------------------------
# access tokens (JWT)
# ---------------------------------------------------------------------------
def create_access_token(*, user_id: str, username: str, role: str) -> str:
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": ACCESS_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising UnauthorizedError on any problem."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Access token has expired", code="token_expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid access token", code="invalid_token") from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise UnauthorizedError("Invalid token type", code="invalid_token")
    return payload


# ---------------------------------------------------------------------------
# refresh tokens (opaque, rotated, stored hashed)
# ---------------------------------------------------------------------------
def generate_refresh_token() -> tuple[str, str]:
    """Return ``(raw_token, sha256_hash)``. Only the hash is ever persisted."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)