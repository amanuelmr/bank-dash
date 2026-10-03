"""Card model.

Only a masked number is persisted. A full PAN is generated at issue time purely
to derive that mask and is then discarded, so a database leak cannot expose
usable card numbers.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_column, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class CardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    EXPIRED = "EXPIRED"


class Card(Base, TimestampMixin):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    card_type: Mapped[str] = mapped_column(String(40), nullable=False)
    card_holder: Mapped[str] = mapped_column(String(150), nullable=False)
    masked_number: Mapped[str] = mapped_column(String(19), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CardStatus] = mapped_column(
        enum_column(CardStatus), default=CardStatus.ACTIVE, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="cards")