"""Loan lifecycle: application, approval, rejection, and repayment."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError
from app.models.base import utcnow
from app.models.loan import Loan, LoanStatus, LoanType
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.user import User
from app.schemas.common import Page
from app.schemas.loan import (
    CreateLoanRequest,
    LoanOut,
    LoanSummaryOut,
    RepayResultOut,
)
from app.services.transaction import (
    CATEGORY_BY_TYPE,
    SYSTEM_USERNAME,
    lock_users_for_update,
    new_transaction_id,
    round_money,
)


def compute_installment(principal: float, annual_rate: float, months: int) -> float:
    """Standard amortised monthly payment."""
    if months <= 0:
        raise BusinessRuleError("Loan duration must be at least one month")
    r = annual_rate / 100 / 12
    if r == 0:
        return round_money(principal / months)
    factor = (1 + r) ** months
    return round_money(principal * r * factor / (factor - 1))


def _loan_dates(loan: Loan) -> tuple:
    start = loan.start_date or utcnow().date()
    return start, start + timedelta(days=30 * loan.loan_duration)


async def list_loans(
    db: AsyncSession, user: User, *, page: int, size: int
) -> Page[LoanOut]:
    total = int(
        await db.scalar(select(func.count()).select_from(Loan).where(Loan.user_id == user.id))
        or 0
    )
    rows = (
        await db.scalars(
            select(Loan)
            .where(Loan.user_id == user.id)
            .order_by(Loan.created_at.desc())
            .offset(page * size)
            .limit(size)
        )
    ).all()
    return Page[LoanOut].build(
        items=[LoanOut.model_validate(loan) for loan in rows],
        total=total,
        page=page,
        size=size,
    )


async def list_all_loans(db: AsyncSession, *, page: int, size: int) -> Page[LoanOut]:
    total = int(await db.scalar(select(func.count()).select_from(Loan)) or 0)
    rows = (
        await db.scalars(
            select(Loan).order_by(Loan.created_at.desc()).offset(page * size).limit(size)
        )
    ).all()
    return Page[LoanOut].build(
        items=[LoanOut.model_validate(loan) for loan in rows],
        total=total,
        page=page,
        size=size,
    )


async def loan_summary(db: AsyncSession, user: User) -> LoanSummaryOut:
    rows = (
        await db.execute(
            select(Loan.loan_type, func.coalesce(func.sum(Loan.amount_left_to_repay), 0.0))
            .where(
                Loan.user_id == user.id,
                Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.APPROVED]),
            )
            .group_by(Loan.loan_type)
        )
    ).all()
    totals = {loan_type: float(total) for loan_type, total in rows}
    personal = totals.get(LoanType.PERSONAL, 0.0)
    corporate = totals.get(LoanType.CORPORATE, 0.0)
    business = totals.get(LoanType.BUSINESS, 0.0)
    return LoanSummaryOut(
        personal_loan=round_money(personal),
        corporate_loan=round_money(corporate),
        business_loan=round_money(business),
        total_outstanding=round_money(personal + corporate + business),
    )


async def get_loan(db: AsyncSession, loan_id: str, *, user_id: str | None = None) -> Loan:
    loan = await db.scalar(select(Loan).where(Loan.id == loan_id))
    if loan is None or (user_id is not None and loan.user_id != user_id):
        raise NotFoundError("Loan not found")
    return loan


async def create_loan(db: AsyncSession, user: User, payload: CreateLoanRequest) -> LoanOut:
    installment = compute_installment(
        payload.loan_amount, payload.interest_rate, payload.loan_duration
    )
    loan = Loan(
        user_id=user.id,
        loan_type=payload.loan_type,
        loan_amount=round_money(payload.loan_amount),
        amount_left_to_repay=round_money(payload.loan_amount),
        installment=installment,
        interest_rate=payload.interest_rate,
        loan_duration=payload.loan_duration,
        status=LoanStatus.PENDING,
    )
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return LoanOut.model_validate(loan)


async def approve_loan(db: AsyncSession, loan_id: str) -> LoanOut:
    loan = await get_loan(db, loan_id)
    if loan.status is not LoanStatus.PENDING:
        raise BusinessRuleError("Only pending loans can be approved")
    loan.status = LoanStatus.ACTIVE
    loan.start_date, loan.end_date = _loan_dates(loan)
    await db.commit()
    await db.refresh(loan)
    return LoanOut.model_validate(loan)


async def reject_loan(db: AsyncSession, loan_id: str) -> LoanOut:
    loan = await get_loan(db, loan_id)
    if loan.status is not LoanStatus.PENDING:
        raise BusinessRuleError("Only pending loans can be rejected")
    loan.status = LoanStatus.REJECTED
    await db.commit()
    await db.refresh(loan)
    return LoanOut.model_validate(loan)


async def repay_loan(
    db: AsyncSession, user: User, loan_id: str, amount: float | None
) -> RepayResultOut:
    """Pay down a loan, debiting the borrower's account.

    Omitting ``amount`` clears the full outstanding balance. The balance is
    locked before the outstanding figure is read so two concurrent repayments
    cannot both see funds that only one of them can have.
    """
    loan = await db.scalar(
        select(Loan).where(Loan.id == loan_id, Loan.user_id == user.id)
    )
    if loan is None:
        raise NotFoundError("Loan not found")
    if loan.status not in (LoanStatus.ACTIVE, LoanStatus.APPROVED):
        raise BusinessRuleError("This loan is not currently repayable")

    locked_users = await lock_users_for_update(db, [user.id])
    locked_user = locked_users[user.id]

    outstanding = round_money(loan.amount_left_to_repay)
    payment = round_money(amount) if amount is not None else outstanding
    if payment <= 0:
        raise BusinessRuleError("Repayment amount must be greater than zero")
    if payment > outstanding:
        payment = outstanding

    if locked_user.account_balance < payment:
        raise BusinessRuleError("Insufficient funds", code="insufficient_funds")

    locked_user.account_balance = round_money(locked_user.account_balance - payment)
    loan.amount_left_to_repay = round_money(outstanding - payment)
    if loan.amount_left_to_repay <= 0:
        loan.status = LoanStatus.PAID

    db.add(
        Transaction(
            transaction_id=new_transaction_id(),
            group_id=loan.id,
            user_id=locked_user.id,
            type=TransactionType.LOAN_REPAYMENT,
            direction=TransactionDirection.OUT,
            amount=payment,
            description=f"Repayment for {loan.loan_type.value}",
            category=CATEGORY_BY_TYPE[TransactionType.LOAN_REPAYMENT],
            status=TransactionStatus.COMPLETED,
            sender_username=locked_user.username,
            receiver_username=SYSTEM_USERNAME,
            occurred_at=utcnow(),
        )
    )

    await db.commit()
    await db.refresh(loan)
    return RepayResultOut(
        loan=LoanOut.model_validate(loan), amount_paid=round_money(payment)
    )