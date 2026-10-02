"""Loan routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import Pagination, get_current_admin, get_current_user, get_pagination
from app.models.user import User
from app.schemas.common import ApiResponse, Page
from app.schemas.loan import (
    CreateLoanRequest,
    LoanOut,
    LoanSummaryOut,
    RepayLoanRequest,
    RepayResultOut,
)
from app.services import loan as loan_service

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("", response_model=ApiResponse[Page[LoanOut]], summary="My loans")
async def list_my_loans(
    pagination: Pagination = Depends(get_pagination),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Page[LoanOut]]:
    page = await loan_service.list_loans(db, user, page=pagination.page, size=pagination.size)
    return ApiResponse(data=page)


@router.get("/summary", response_model=ApiResponse[LoanSummaryOut], summary="Outstanding by type")
async def summary(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> ApiResponse[LoanSummaryOut]:
    return ApiResponse(data=await loan_service.loan_summary(db, user))


@router.get("/all", response_model=ApiResponse[Page[LoanOut]], summary="Every loan (admin)")
async def list_all_loans(
    pagination: Pagination = Depends(get_pagination),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Page[LoanOut]]:
    page = await loan_service.list_all_loans(db, page=pagination.page, size=pagination.size)
    return ApiResponse(data=page)


@router.post(
    "",
    response_model=ApiResponse[LoanOut],
    status_code=status.HTTP_201_CREATED,
    summary="Apply for a loan",
)
async def create_loan(
    payload: CreateLoanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LoanOut]:
    loan = await loan_service.create_loan(db, user, payload)
    return ApiResponse(message="Loan application submitted", data=loan)


@router.get("/{loan_id}", response_model=ApiResponse[LoanOut], summary="One loan")
async def get_loan(
    loan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LoanOut]:
    loan = await loan_service.get_loan(db, loan_id, user_id=user.id)
    return ApiResponse(data=LoanOut.model_validate(loan))


@router.post("/{loan_id}/approve", response_model=ApiResponse[LoanOut], summary="Approve (admin)")
async def approve_loan(
    loan_id: str,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LoanOut]:
    loan = await loan_service.approve_loan(db, loan_id)
    return ApiResponse(message="Loan approved", data=loan)


@router.post("/{loan_id}/reject", response_model=ApiResponse[LoanOut], summary="Reject (admin)")
async def reject_loan(
    loan_id: str,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LoanOut]:
    loan = await loan_service.reject_loan(db, loan_id)
    return ApiResponse(message="Loan rejected", data=loan)


@router.post(
    "/{loan_id}/repay",
    response_model=ApiResponse[RepayResultOut],
    summary="Repay a loan (defaults to the full outstanding amount)",
)
async def repay_loan(
    loan_id: str,
    payload: RepayLoanRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RepayResultOut]:
    result = await loan_service.repay_loan(db, user, loan_id, payload.amount if payload else None)
    return ApiResponse(message="Repayment received", data=result)