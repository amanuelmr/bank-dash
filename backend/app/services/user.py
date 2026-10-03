"""User profile, preferences, account summary, balance history, investments."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.base import utcnow
from app.models.loan import Loan, LoanStatus, LoanType
from app.models.transaction import Transaction, TransactionDirection, TransactionStatus
from app.models.user import User, UserPreference
from app.schemas.user import (
    AccountSummaryOut,
    InvestmentSummaryOut,
    PublicUserOut,
    SeriesPoint,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
)


async def get_user_by_username(db: AsyncSession, username: str) -> User:
    user = await db.scalar(select(User).where(User.username == username.strip().lower()))
    if user is None:
        raise NotFoundError("User not found")
    return user


async def get_public_profile(db: AsyncSession, username: str) -> PublicUserOut:
    return PublicUserOut.model_validate(await get_user_by_username(db, username))


async def update_profile(db: AsyncSession, user: User, payload: UpdateProfileRequest) -> User:
    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"]:
        clash = await db.scalar(
            select(User).where(User.email == data["email"], User.id != user.id)
        )
        if clash is not None:
            raise ConflictError("That email is already registered")

    for field, value in data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def update_preferences(
    db: AsyncSession, user: User, payload: UpdatePreferencesRequest
) -> UserPreference:
    if user.preferences is None:
        user.preferences = UserPreference()
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user.preferences, field, value)
    await db.commit()
    await db.refresh(user)
    assert user.preferences is not None  # noqa: S101 - narrowed for the type checker
    return user.preferences


async def account_summary(db: AsyncSession, user: User) -> AccountSummaryOut:
    totals = (
        await db.execute(
            select(
                Transaction.direction,
                func.coalesce(func.sum(Transaction.amount), 0.0),
            )
            .where(
                Transaction.user_id == user.id,
                Transaction.status == TransactionStatus.COMPLETED,
            )
            .group_by(Transaction.direction)
        )
    ).all()
    by_direction = {d: float(total) for d, total in totals}

    income = by_direction.get(TransactionDirection.IN, 0.0)
    expense = by_direction.get(TransactionDirection.OUT, 0.0)
    return AccountSummaryOut(
        account_balance=round(user.account_balance, 2),
        total_income=round(income, 2),
        total_expense=round(expense, 2),
        total_savings=round(income - expense, 2),
    )


def build_balance_series(
    transactions: list[Transaction],
    current_balance: float,
    months: int,
    *,
    now: datetime | None = None,
) -> list[SeriesPoint]:
    """Derive a month-end balance series by walking the ledger backwards.

    Rather than generating synthetic numbers, this reconstructs the balance
    that the account actually held at each month boundary: the balance at time
    ``t`` is the current balance minus every movement that happened after it.
    """
    reference = now or utcnow()

    signed: list[tuple[datetime, float]] = []
    for tx in transactions:
        delta = tx.amount if tx.direction is TransactionDirection.IN else -tx.amount
        signed.append((tx.occurred_at, delta))

    points: list[SeriesPoint] = []
    for offset in range(months - 1, -1, -1):
        year = reference.year
        month = reference.month - offset
        while month < 1:
            month += 12
            year -= 1

        # First instant of the month *after* the one being reported.
        boundary = (
            datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        )

        net_after = sum(delta for occurred, delta in signed if occurred >= boundary)
        points.append(
            SeriesPoint(
                period=f"{year:04d}-{month:02d}",
                value=round(current_balance - net_after, 2),
            )
        )
    return points


async def loan_totals(db: AsyncSession, user_id: str) -> dict[LoanType, float]:
    rows = (
        await db.execute(
            select(Loan.loan_type, func.coalesce(func.sum(Loan.amount_left_to_repay), 0.0))
            .where(
                Loan.user_id == user_id,
                Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.APPROVED]),
            )
            .group_by(Loan.loan_type)
        )
    ).all()
    return {loan_type: float(total) for loan_type, total in rows}


# ---------------------------------------------------------------------------
# investments
# ---------------------------------------------------------------------------
def build_investment_summary(
    user: User, years: int = 5, months: int = 8, *, now: datetime | None = None
) -> InvestmentSummaryOut:
    """Synthesise an investment summary.

    There is no holdings ledger behind this yet - the frontend has no UI for
    managing positions - so the figures are generated from a PRNG seeded by
    the username. Seeding by username keeps them stable across requests and
    identical for a given user, instead of flickering on every page load.
    Replace with real holdings queries when that data model exists.
    """
    import random

    rnd = random.Random(f"bankdash-investments::{user.username}")
    reference = now or utcnow()

    yearly: list[SeriesPoint] = []
    base = rnd.uniform(4_000, 12_000)
    for offset in range(years - 1, -1, -1):
        year = reference.year - offset
        growth = rnd.uniform(1.02, 1.28)
        base *= growth
        yearly.append(SeriesPoint(period=f"{year:04d}", value=round(base, 2)))

    monthly_revenue: list[SeriesPoint] = []
    monthly_base = rnd.uniform(400, 1_500)
    for offset in range(months - 1, -1, -1):
        year = reference.year
        month = reference.month - offset
        while month < 1:
            month += 12
            year -= 1
        monthly_base *= rnd.uniform(0.92, 1.18)
        monthly_revenue.append(
            SeriesPoint(period=f"{year:04d}-{month:02d}", value=round(monthly_base, 2))
        )

    total_investment = round(sum(p.value for p in yearly), 2)
    number_of_investments = rnd.randint(400, 2600)

    return InvestmentSummaryOut(
        total_investment=total_investment,
        rate_of_return=round(rnd.uniform(4.5, 24.0), 2),
        number_of_investments=number_of_investments,
        yearly_investments=yearly,
        monthly_revenue=monthly_revenue,
    )
