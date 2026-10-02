"""User profile, preferences, and dashboard summaries."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.user import (
    AccountSummaryOut,
    InvestmentSummaryOut,
    PreferencesOut,
    PreferencesRequest,
    PublicUserOut,
    UpdateProfileRequest,
    UserOut,
)
from app.services import user as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ApiResponse[UserOut], summary="The signed-in user")
async def read_me(user: User = Depends(get_current_user)) -> ApiResponse[UserOut]:
    return ApiResponse(data=UserOut.model_validate(user))


@router.put("/me", response_model=ApiResponse[UserOut], summary="Update the signed-in user")
async def update_me(
    payload: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserOut]:
    updated = await user_service.update_profile(db, user, payload)
    return ApiResponse(message="Profile updated", data=UserOut.model_validate(updated))


@router.put(
    "/me/preferences",
    response_model=ApiResponse[PreferencesOut],
    summary="Update notification and locale preferences",
)
async def update_my_preferences(
    payload: PreferencesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PreferencesOut]:
    preferences = await user_service.update_preferences(db, user, payload)
    return ApiResponse(
        message="Preferences updated", data=PreferencesOut.model_validate(preferences)
    )


@router.get(
    "/me/summary",
    response_model=ApiResponse[AccountSummaryOut],
    summary="Balance, income, expense and savings totals",
)
async def my_summary(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ApiResponse[AccountSummaryOut]:
    return ApiResponse(data=await user_service.account_summary(db, user))


@router.get(
    "/me/investment-summary",
    response_model=ApiResponse[InvestmentSummaryOut],
    summary="Investment totals and time series",
)
async def my_investment_summary(
    years: int = Query(5, ge=1, le=30),
    months: int = Query(8, ge=1, le=36),
    user: User = Depends(get_current_user),
) -> ApiResponse[InvestmentSummaryOut]:
    return ApiResponse(data=user_service.build_investment_summary(user, years, months))


@router.get(
    "/{username}", response_model=ApiResponse[PublicUserOut], summary="Public profile by username"
)
async def public_profile(
    username: str, db: AsyncSession = Depends(get_db)
) -> ApiResponse[PublicUserOut]:
    return ApiResponse(data=await user_service.get_public_profile(db, username))