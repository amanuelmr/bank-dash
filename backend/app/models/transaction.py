"""Transaction model - a double-entry ledger row.

Every movement writes one row *per party* rather than a single shared row:

* the sender gets an ``OUT`` row,
* the receiver gets an ``IN`` row.

Both rows share ``group_id`` so the pair stays traceable. This keeps
``direction`` correct per viewer (it cannot be derived at read time from a
single shared row) and makes every per-user query a simple indexed lookup on
``user_id``.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_column, utcnow, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class TransactionType(StrEnum):
    TRANSFER = "transfer"
    SHOPPING = "shopping"
    DEPOSIT = "deposit"
    SERVICE = "service"
    LOAN_REPAYMENT = "loan_repayment"


class TransactionDirection(StrEnum):
    IN = "IN"
    OUT = "OUT"


class TransactionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    #: Human-readable code shown in the UI, e.g. "TXN-9F3A2C71".
    transaction_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    #: Shared by both legs of a transfer.
    group_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[TransactionType] = mapped_column(
        enum_column(TransactionType), nullable=False
    )
    direction: Mapped[TransactionDirection] = mapped_column(
        enum_column(TransactionDirection), nullable=False
    )
    #: Always positive - the sign lives in ``direction``.
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    category: Mapped[str] = mapped_column(String(60), default="general", nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        enum_column(TransactionStatus), default=TransactionStatus.COMPLETED, nullable=False
    )

    sender_username: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    receiver_username: Mapped[str] = mapped_column(String(60), index=True, nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, index=True, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="transactions")

    __table_args__ = (Index("ix_transactions_user_occurred", "user_id", "occurred_at"),)