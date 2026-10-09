"""Transaction routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import Pagination, get_current_user, get_pagination
from app.models.transaction import TransactionDirection
from app.models.user import User
from app.schemas.common import ApiResponse, Page
from app.schemas.transaction import (
    CreateTransactionRequest,
    DepositRequest,
    TransactionOut,
    TransferRecipientOut,
)
from app.schemas.user import CashflowPoint, CategoryTotal, SeriesPoint
from app.services import transaction as tx_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=ApiResponse[Page[TransactionOut]], summary="List my transactions")
async def list_all(
    pagination: Pagination = Depends(get_pagination),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Page[TransactionOut]]:
    page = await tx_service.list_transactions(
        db, user, page=pagination.page, size=pagination.size
    )
    return ApiResponse(data=page)


@router.get("/incomes", response_model=ApiResponse[Page[TransactionOut]], summary="Money in")
async def list_incomes(
    pagination: Pagination = Depends(get_pagination),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Page[TransactionOut]]:
    page = await tx_service.list_transactions(
        db,
        user,
        page=pagination.page,
        size=pagination.size,
        direction=TransactionDirection.IN,
    )
    return ApiResponse(data=page)


@router.get("/expenses", response_model=ApiResponse[Page[TransactionOut]], summary="Money out")
async def list_expenses(
    pagination: Pagination = Depends(get_pagination),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Page[TransactionOut]]:
    page = await tx_service.list_transactions(
        db,
        user,
        page=pagination.page,
        size=pagination.size,
        direction=TransactionDirection.OUT,
    )
    return ApiResponse(data=page)


@router.get(
    "/balance-history",
    response_model=ApiResponse[list[SeriesPoint]],
    summary="Month-end balance series",
)
async def balance_history(
    months: int = Query(12, ge=1, le=60),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[SeriesPoint]]:
    return ApiResponse(data=await tx_service.balance_history(db, user, months))


@router.get(
    "/transfer-recipients",
    response_model=ApiResponse[list[TransferRecipientOut]],
    summary="People available to transfer to",
)
async def transfer_recipients(
    limit: int = Query(6, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[TransferRecipientOut]]:
    return ApiResponse(data=await tx_service.transfer_recipients(db, user, limit))


@router.post(
    "",
    response_model=ApiResponse[TransactionOut],
    status_code=status.HTTP_201_CREATED,
    summary="Pay, transfer, or shop",
)
async def create_transaction(
    payload: CreateTransactionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TransactionOut]:
    entry = await tx_service.create_transfer(db, user, payload)
    return ApiResponse(message="Transaction recorded", data=TransactionOut.model_validate(entry))


@router.post(
    "/deposit",
    response_model=ApiResponse[TransactionOut],
    status_code=status.HTTP_201_CREATED,
    summary="Add funds to the account",
)
async def create_deposit(
    payload: DepositRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TransactionOut]:
    entry = await tx_service.create_deposit(db, user, payload)
    return ApiResponse(message="Deposit recorded", data=TransactionOut.model_validate(entry))


@router.get(
    "/summary/categories",
    response_model=ApiResponse[list[CategoryTotal]],
    summary="Spend grouped by category",
)
async def spend_by_category(
    months: int = Query(12, ge=1, le=36),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[CategoryTotal]]:
    return ApiResponse(data=await tx_service.spend_by_category(db, user, months))


@router.get(
    "/summary/monthly",
    response_model=ApiResponse[list[SeriesPoint]],
    summary="Spend grouped by month",
)
async def spend_by_month(
    months: int = Query(6, ge=1, le=36),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[SeriesPoint]]:
    return ApiResponse(data=await tx_service.spend_by_month(db, user, months))


@router.get(
    "/summary/cashflow",
    response_model=ApiResponse[list[CashflowPoint]],
    summary="Money in and out per month",
)
async def cashflow_by_month(
    months: int = Query(6, ge=1, le=36),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[CashflowPoint]]:
    return ApiResponse(data=await tx_service.cashflow_by_month(db, user, months))


@router.get(
    "/{transaction_id}", response_model=ApiResponse[TransactionOut], summary="One transaction"
)
async def get_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TransactionOut]:
    entry = await tx_service.get_transaction(db, user, transaction_id)
    return ApiResponse(data=entry)