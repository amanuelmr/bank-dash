"""Registration, login, token refresh, and password change."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.base import utcnow
from app.models.user import RefreshToken, User, UserPreference, UserRole
from app.schemas.auth import TokenPair
from app.schemas.user import RegisterRequest


async def _issue_token_pair(db: AsyncSession, user: User) -> TokenPair:
    """Mint a new access/refresh pair and persist the refresh token's hash."""
    raw_refresh, token_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=refresh_token_expiry(),
        )
    )
    await db.flush()

    return TokenPair(
        access_token=create_access_token(
            user_id=user.id, username=user.username, role=user.role.value
        ),
        refresh_token=raw_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    existing = await db.scalar(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if existing is not None:
        field = "username" if existing.username == payload.username else "email"
        raise ConflictError(f"That {field} is already registered")

    user = User(
        name=payload.name,
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        date_of_birth=payload.date_of_birth,
        permanent_address=payload.permanent_address,
        present_address=payload.present_address,
        postal_code=payload.postal_code,
        city=payload.city,
        country=payload.country,
        profile_picture=payload.profile_picture,
        role=UserRole.USER,
        account_balance=0.0,
    )
    user.preferences = UserPreference(**payload.preferences.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, username: str, password: str) -> tuple[User, TokenPair]:
    user = await db.scalar(select(User).where(User.username == username.strip().lower()))
    # Same error for unknown user and bad password - don't leak which usernames exist.
    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid username or password")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")

    tokens = await _issue_token_pair(db, user)
    await db.commit()
    return user, tokens


async def rotate_refresh_token(db: AsyncSession, raw_token: str) -> tuple[User, TokenPair]:
    """Exchange a refresh token for a fresh pair, revoking the old one.

    Rotation means a stolen refresh token is usable at most once; presenting
    an already-revoked token is treated as a compromise and rejected.
    """
    token_hash = hash_refresh_token(raw_token)
    record = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if record is None:
        raise UnauthorizedError("Invalid refresh token")
    if record.revoked_at is not None:
        raise UnauthorizedError("Refresh token has already been used")
    if record.expires_at < utcnow():
        raise UnauthorizedError("Refresh token has expired", code="token_expired")

    user = await db.get(User, record.user_id)
    if user is None:
        raise NotFoundError("User no longer exists")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")

    record.revoked_at = utcnow()
    tokens = await _issue_token_pair(db, user)
    await db.commit()
    return user, tokens


async def change_password(
    db: AsyncSession,
    user: User,
    *,
    current_password: str,
    new_password: str,
    two_factor_enabled: bool | None = None,
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise UnauthorizedError("Current password is incorrect")

    user.hashed_password = hash_password(new_password)
    if two_factor_enabled is not None and user.preferences is not None:
        user.preferences.two_factor_authentication = two_factor_enabled

    # Force every existing session to re-authenticate with the new password.
    await db.execute(
        RefreshToken.__table__.update()
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    await db.commit()


async def logout(db: AsyncSession, user: User, raw_token: str | None) -> None:
    """Revoke the presented refresh token, or every token for the user."""
    now = utcnow()
    if raw_token:
        await db.execute(
            RefreshToken.__table__.update()
            .where(
                RefreshToken.user_id == user.id,
                RefreshToken.token_hash == hash_refresh_token(raw_token),
            )
            .values(revoked_at=now)
        )
    else:
        await db.execute(
            RefreshToken.__table__.update()
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
    await db.commit()

