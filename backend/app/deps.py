"""Shared FastAPI dependencies: bearer auth, the current user, and pagination."""

from dataclasses import dataclass

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="JWT access token issued by POST /api/v1/auth/login",
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user, or raise 401."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Authorization header is missing")

    payload = decode_access_token(credentials.credentials)
    user = await db.get(User, payload.get("sub"))
    if user is None:
        raise UnauthorizedError("User no longer exists")
    if not user.is_active:
        raise ForbiddenError("Account is disabled")
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.ADMIN:
        raise ForbiddenError("Administrator privileges required")
    return user


@dataclass(frozen=True)
class Pagination:
    page: int
    size: int

    @property
    def offset(self) -> int:
        return self.page * self.size


async def get_pagination(
    page: int = Query(0, ge=0, description="Zero-indexed page number"),
    size: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Items per page",
    ),
) -> Pagination:
    return Pagination(page=page, size=size)