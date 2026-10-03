"""Card routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import Pagination, get_current_user, get_pagination
from app.models.user import User
from app.schemas.card import CardOut, CreateCardRequest
from app.schemas.common import ApiResponse, Page
from app.services import card as card_service

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=ApiResponse[Page[CardOut]], summary="List my cards")
async def list_cards(
    pagination: Pagination = Depends(get_pagination),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Page[CardOut]]:
    page = await card_service.list_cards(db, user, page=pagination.page, size=pagination.size)
    return ApiResponse(data=page)


@router.post(
    "",
    response_model=ApiResponse[CardOut],
    status_code=status.HTTP_201_CREATED,
    summary="Issue a new card",
)
async def create_card(
    payload: CreateCardRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CardOut]:
    card = await card_service.create_card(db, user, payload)
    return ApiResponse(message="Card created", data=card)


@router.get("/{card_id}", response_model=ApiResponse[CardOut], summary="One card")
async def get_card(
    card_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CardOut]:
    return ApiResponse(data=await card_service.get_card(db, user, card_id))


@router.delete("/{card_id}", response_model=ApiResponse[None], summary="Delete a card")
async def delete_card(
    card_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    await card_service.delete_card(db, user, card_id)
    return ApiResponse(message="Card deleted", data=None)