"""Authentication routes.

Tokens are delivered as httpOnly cookies rather than in the response body, so a
script injected into the page cannot read them. The API still accepts an
``Authorization: Bearer`` header (see :func:`app.deps.get_current_user`), which
keeps CLI clients and the smoke script working unchanged.
"""

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import UnauthorizedError, app_error_response
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RefreshRequest
from app.schemas.common import ApiResponse
from app.schemas.user import RegisterRequest, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _cookie_specs() -> dict[str, tuple[str, int]]:
    """Cookie name -> (path, max_age_seconds).

    The access token goes to "/" because it authenticates every endpoint. The
    refresh token is scoped to the auth routes, which are the only places it is
    ever presented - a cookie on "/" rides along with every API call, so any
    endpoint that logs or reflects request headers would expose a 30-day
    credential.
    """
    return {
        settings.access_cookie_name: ("/", settings.access_token_expire_minutes * 60),
        settings.refresh_cookie_name: (
            settings.auth_cookie_path,
            settings.refresh_token_expire_days * 86400,
        ),
    }


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    values = {
        settings.access_cookie_name: access_token,
        settings.refresh_cookie_name: refresh_token,
    }
    for name, (path, max_age) in _cookie_specs().items():
        response.set_cookie(
            name,
            values[name],
            max_age=max_age,
            path=path,
            httponly=True,  # unreadable from JavaScript - the point of the change
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            domain=settings.cookie_domain,
        )


def _clear_auth_cookies(response: Response) -> None:
    for name, (path, _) in _cookie_specs().items():
        response.delete_cookie(
            name,
            # The path must match the one the cookie was set with, or the
            # browser keeps the original and the expiry is ignored.
            path=path,
            domain=settings.cookie_domain,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )


def _unauthorized_and_expired(exc: UnauthorizedError) -> JSONResponse:
    """Build a 401 that also expires the auth cookies.

    Two traps make this awkward enough to be worth a helper:

    * Headers set on an injected `Response` are discarded once an exception
      handler runs, so the failure has to be *returned* rather than raised.
    * `JSONResponse(headers=...)` takes a mapping, and both expiries share the
      name `set-cookie` - a dict would silently keep only one. The raw header
      list is the only representation that carries both.
    """
    response = app_error_response(exc)
    scratch = Response()
    _clear_auth_cookies(scratch)
    response.raw_headers.extend(scratch.raw_headers)
    return response


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
) -> ApiResponse[UserOut] | JSONResponse:
    """The browser sends no body here - the refresh cookie travels automatically."""
    raw_token = payload.refresh_token if payload else request.cookies.get(
        settings.refresh_cookie_name
    )

    try:
        if not raw_token:
            raise UnauthorizedError("No refresh token supplied")
        user, tokens = await auth_service.rotate_refresh_token(db, raw_token)
    except UnauthorizedError as exc:
        # Returned rather than raised so the cookie expiry survives.
        #
        # Clearing matters because an httpOnly cookie cannot be deleted by the
        # browser. Without this the dead cookie lingers for its full 30-day
        # lifetime, and every API call first pays a doomed refresh round-trip.
        return _unauthorized_and_expired(exc)

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
