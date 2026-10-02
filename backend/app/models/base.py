"""Shared column helpers and mixins for the ORM models."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    """Naive UTC timestamp.

    Timestamps are stored naive so SQLite and Postgres behave identically -
    a ``DateTime(timezone=True)`` column silently loses tzinfo when read back
    from SQLite, which makes naive/aware comparisons explode later.
    Schemas re-attach UTC on the way out (see ``UtcDateTime``).
    """
    return datetime.now(UTC).replace(tzinfo=None)


def uuid_pk() -> str:
    return str(uuid.uuid4())


def enum_column[E](enum_cls: type[E], **kwargs: Any) -> SAEnum:
    """A portable enum column.

    ``native_enum=False`` keeps this a VARCHAR so the same schema works on
    SQLite and Postgres without an ALTER TYPE migration, and
    ``values_callable`` stores the member *value* rather than its name.
    """
    return SAEnum(
        enum_cls,
        values_callable=lambda e: [m.value for m in e],
        native_enum=False,
        length=40,
        **kwargs,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )


__all__ = [
    "Base",
    "Mapped",
    "String",
    "TimestampMixin",
    "enum_column",
    "mapped_column",
    "utcnow",
    "uuid_pk",
]