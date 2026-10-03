"""Company model - drives the investments / trending-stock widgets."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(12), nullable=False)
    sector: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    change_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)