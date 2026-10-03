"""Authentication routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenPair,
)
from app.schemas.common import ApiResponse
from app.schemas.user import RegisterRequest, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


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
    "/login", response_model=ApiResponse[TokenPair], summary="Exchange credentials for tokens"
)
async def login(
    payload: LoginRequest, db: AsyncSession = Depends(get_db)
) -> ApiResponse[TokenPair]:
    _, tokens = await auth_service.authenticate(db, payload.username, payload.password)
    return ApiResponse(message="Signed in", data=tokens)


@router.post(
    "/refresh", response_model=ApiResponse[TokenPair], summary="Rotate a refresh token"
)
async def refresh(
    payload: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> ApiResponse[TokenPair]:
    _, tokens = await auth_service.rotate_refresh_token(db, payload.refresh_token)
    return ApiResponse(message="Token refreshed", data=tokens)


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


@router.post("/logout", response_model=ApiResponse[None], summary="Revoke refresh tokens")
async def logout(
    payload: RefreshRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    await auth_service.logout(db, user, payload.refresh_token if payload else None)
    return ApiResponse(message="Signed out", data=None)