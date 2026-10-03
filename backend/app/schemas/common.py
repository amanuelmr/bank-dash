"""Shared response wrappers: the standard envelope and the standard page object."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer
from pydantic.alias_generators import to_camel


def _serialize_utc(value: datetime) -> str:
    """Render a stored naive-UTC timestamp as an unambiguous ISO-8601 instant.

    Without the explicit ``Z`` the browser's ``new Date()`` would parse it as
    *local* time and every timestamp would render shifted by the user's offset.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


#: A datetime that always serialises as ``2026-01-15T10:30:00Z``.
UtcDateTime = Annotated[datetime, PlainSerializer(_serialize_utc, return_type=str)]


class CamelModel(BaseModel):
    """Base model that serialises snake_case fields as camelCase.

    Fields are declared in Pythonic snake_case and exposed on the wire as
    camelCase (``account_balance`` -> ``accountBalance``). FastAPI serialises
    response models with ``by_alias=True``, so declared responses need nothing
    extra; request bodies are accepted under either name.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ApiResponse[T](CamelModel):
    """The single response shape every endpoint returns."""

    success: bool = True
    message: str | None = None
    data: T | None = None


class Page[T](CamelModel):
    """Uniform pagination payload for every list endpoint."""

    items: list[T] = Field(default_factory=list)
    page: int
    size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def build(cls, *, items: list[T], total: int, page: int, size: int) -> "Page[T]":
        total_pages = -(-total // size) if size else 0  # ceil division
        return cls(
            items=items,
            page=page,
            size=size,
            total_items=total,
            total_pages=total_pages,
            has_next=page + 1 < total_pages,
            has_previous=page > 0,
        )