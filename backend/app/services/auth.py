"""Registration, login, token refresh, and password change."""

import logging

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
from app.models.base import utcnow, uuid_pk
from app.models.user import RefreshToken, User, UserPreference, UserRole
from app.schemas.auth import TokenPair
from app.schemas.user import RegisterRequest

logger = logging.getLogger(__name__)


async def _revoke_family(db: AsyncSession, user_id: str, family_id: str) -> int:
    """Revoke every live token descended from one sign-in. Returns the count."""
    result = await db.execute(
        RefreshToken.__table__.update()
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=utcnow())
    )
    await db.commit()
    return result.rowcount or 0


async def _issue_token_pair(
    db: AsyncSession, user: User, *, family_id: str | None = None
) -> TokenPair:
    """Mint a new access/refresh pair and persist the refresh token's hash.

    `family_id` is omitted on sign-in, which starts a new family, and passed on
    rotation so the chain stays linked.
    """
    raw_refresh, token_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            family_id=family_id or uuid_pk(),
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
        # A spent token came back. Rotation means a token is single-use, so the
        # only way to present one twice is that two parties hold it: either the
        # token was stolen, or the legitimate client replayed it after an
        # attack. We cannot tell which, and the cost of guessing wrong is low -
        # the user signs in again - while the cost of guessing wrong the other
        # way is an attacker holding a renewable session.
        #
        # So the whole family is revoked, not just this token. Revoking only the
        # presented token would leave every token the thief had already rotated
        # to still working, which is the entire point of stealing one.
        await _revoke_family(db, record.user_id, record.family_id)
        logger.warning(
            "refresh token replay detected; revoked the whole session family",
            extra={"user_id": record.user_id, "family_id": record.family_id},
        )
        raise UnauthorizedError("Refresh token has already been used")

    if record.expires_at < utcnow():
        raise UnauthorizedError("Refresh token has expired", code="token_expired")

    user = await db.get(User, record.user_id)
    if user is None:
        raise NotFoundError("User no longer exists")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")

    record.revoked_at = utcnow()
    # Inherit the family so the new token is covered by any later replay.
    tokens = await _issue_token_pair(db, user, family_id=record.family_id)
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
    """Revoke only the refresh token this request presented.

    When no token is presented there is nothing to revoke for this session, and
    the cookies are expired client-side regardless. The earlier version fell back
    to revoking *every* outstanding token for the user, so one device missing its
    cookie - or someone clearing cookies partially - silently signed them out on
    every other device too. Signing out is a per-device action; "sign out
    everywhere" is a different feature and should be asked for explicitly rather
    than falling out of a missing cookie.
    """
    if not raw_token:
        return

    record = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.token_hash == hash_refresh_token(raw_token),
        )
    )
    if record is None:
        return

    # Revoking the family is still per-device - a family is one device's session
    # chain - but it also kills the tokens that chain had already rotated to.
    # Revoking only the presented token would leave those alive, so a thief who
    # stole any link of the chain keeps a working session after the real user
    # signs out.
    await _revoke_family(db, user.id, record.family_id)

