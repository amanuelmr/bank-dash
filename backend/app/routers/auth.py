"""Authentication routes.

Tokens are delivered as httpOnly cookies rather than in the response body, so a
script injected into the page cannot read them. The API still accepts an
``Authorization: Bearer`` header (see :func:`app.deps.get_current_user`), which
keeps CLI clients and the smoke script working unchanged.
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import UnauthorizedError
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RefreshRequest
from app.schemas.common import ApiResponse
from app.schemas.user import RegisterRequest, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    common = {
        "httponly": True,  # unreadable from JavaScript - the point of the change
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
        "domain": settings.cookie_domain,
        "path": "/",
    }
    response.set_cookie(
        settings.access_cookie_name,
        access_token,
        max_age=settings.access_token_expire_minutes * 60,
        **common,
    )
    response.set_cookie(
        settings.refresh_cookie_name,
        refresh_token,
        max_age=settings.refresh_token_expire_days * 86400,
        **common,
    )


def _clear_auth_cookies(response: Response) -> None:
    for name in (settings.access_cookie_name, settings.refresh_cookie_name):
        response.delete_cookie(
            name,
            path="/",
            domain=settings.cookie_domain,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )


@router.post(
    "/register",
    response_model=ApiResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> ApiResponse[UserOut]:
    user = await auth_service.register_user(db, payload)
    return ApiResponse(message="Account created", data=UserOut.model_validate(user))


@router.post(
    "/login",
    response_model=ApiResponse[UserOut],
    summary="Sign in; sets httpOnly auth cookies",
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserOut]:
    user, tokens = await auth_service.authenticate(db, payload.username, payload.password)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return ApiResponse(message="Signed in", data=UserOut.model_validate(user))


@router.post(
    "/refresh",
    response_model=ApiResponse[UserOut],
    summary="Rotate the refresh cookie and re-issue the access cookie",
)
async def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserOut]:
    """The browser sends no body here - the refresh cookie travels automatically."""
    raw_token = payload.refresh_token if payload else request.cookies.get(
        settings.refresh_cookie_name
    )
    if not raw_token:
        raise UnauthorizedError("No refresh token supplied")

    user, tokens = await auth_service.rotate_refresh_token(db, raw_token)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return ApiResponse(message="Session refreshed", data=UserOut.model_validate(user))


@router.post(
    "/change-password",
    response_model=ApiResponse[None],
    summary="Change the signed-in user's password",
)
async def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    await auth_service.change_password(
        db,
        user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        two_factor_enabled=payload.two_factor_enabled,
    )
    return ApiResponse(message="Password updated", data=None)


@router.post(
    "/logout", response_model=ApiResponse[None], summary="Revoke tokens and clear cookies"
)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    await auth_service.logout(db, user, raw_token)
    _clear_auth_cookies(response)
    return ApiResponse(message="Signed out", data=None)