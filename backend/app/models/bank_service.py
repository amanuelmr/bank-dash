"""Bank service model - the catalogue behind the /services page."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, enum_column, uuid_pk


class BankServiceStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class BankService(Base, TimestampMixin):
    __tablename__ = "bank_services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    details: Mapped[str] = mapped_column(Text, default="", nullable=False)
    type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    status: Mapped[BankServiceStatus] = mapped_column(
        enum_column(BankServiceStatus), default=BankServiceStatus.ACTIVE, nullable=False
    )
    number_of_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)