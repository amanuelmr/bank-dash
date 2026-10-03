"""Loan model."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_column, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class LoanStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    PAID = "PAID"


class LoanType(StrEnum):
    PERSONAL = "Personal Loan"
    CORPORATE = "Corporate Loan"
    BUSINESS = "Business Loan"


class Loan(Base, TimestampMixin):
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    loan_type: Mapped[LoanType] = mapped_column(enum_column(LoanType), nullable=False)
    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    amount_left_to_repay: Mapped[float] = mapped_column(Float, nullable=False)
    installment: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    loan_duration: Mapped[int] = mapped_column(Integer, nullable=False)  # months
    status: Mapped[LoanStatus] = mapped_column(
        enum_column(LoanStatus), default=LoanStatus.PENDING, nullable=False
    )

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped[User] = relationship(back_populates="loans")