"""Card issuing and queries."""

from __future__ import annotations

import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.card import Card, CardStatus
from app.models.user import User
from app.schemas.card import CardOut, CreateCardRequest
from app.schemas.common import Page


def generate_masked_number() -> str:
    """Return a display-only card number such as ``**** **** **** 4821``.

    The last four digits are drawn at random and that is the only part ever
    persisted - the full number is never generated or stored, so the database
    holds nothing that could be used to make a payment.
    """
    last_four = f"{secrets.randbelow(10_000):04d}"
    return f"**** **** **** {last_four}"


async def list_cards(db: AsyncSession, user: User, *, page: int, size: int) -> Page[CardOut]:
    total = int(
        await db.scalar(select(func.count()).select_from(Card).where(Card.user_id == user.id))
        or 0
    )
    rows = (
        await db.scalars(
            select(Card)
            .where(Card.user_id == user.id)
            .order_by(Card.created_at.desc())
            .offset(page * size)
            .limit(size)
        )
    ).all()
    return Page[CardOut].build(
        items=[CardOut.model_validate(c) for c in rows], total=total, page=page, size=size
    )


async def get_card(db: AsyncSession, user: User, card_id: str) -> CardOut:
    card = await db.scalar(select(Card).where(Card.id == card_id, Card.user_id == user.id))
    if card is None:
        raise NotFoundError("Card not found")
    return CardOut.model_validate(card)


async def create_card(db: AsyncSession, user: User, payload: CreateCardRequest) -> CardOut:
    card = Card(
        user_id=user.id,
        card_type=payload.card_type.strip(),
        card_holder=payload.card_holder.strip(),
        masked_number=generate_masked_number(),
        balance=round(payload.balance, 2),
        expiry_date=payload.expiry_date,
        status=CardStatus.ACTIVE,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return CardOut.model_validate(card)


async def delete_card(db: AsyncSession, user: User, card_id: str) -> None:
    card = await db.scalar(select(Card).where(Card.id == card_id, Card.user_id == user.id))
    if card is None:
        raise NotFoundError("Card not found")
    await db.delete(card)
    await db.commit()