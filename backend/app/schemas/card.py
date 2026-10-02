"""Card schemas."""

from datetime import date

from pydantic import Field

from app.models.card import CardStatus
from app.schemas.common import CamelModel, UtcDateTime


class CreateCardRequest(CamelModel):
    card_type: str = Field(min_length=1, max_length=40)
    card_holder: str = Field(min_length=1, max_length=150)
    balance: float = Field(default=0.0, ge=0)
    expiry_date: date
    passcode: str = Field(min_length=4, max_length=12)


class CardOut(CamelModel):
    id: str
    card_type: str
    card_holder: str
    masked_number: str
    balance: float
    expiry_date: date
    status: CardStatus
    created_at: UtcDateTime