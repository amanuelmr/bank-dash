"""Transaction schemas."""

from pydantic import Field

from app.models.transaction import TransactionDirection, TransactionStatus, TransactionType
from app.schemas.common import CamelModel, UtcDateTime


class CreateTransactionRequest(CamelModel):
    type: TransactionType
    amount: float = Field(gt=0)
    description: str | None = None
    receiver_username: str | None = None

    def resolved_description(self, sender_username: str, receiver_username: str | None) -> str:
        if self.description:
            return self.description
        if self.type is TransactionType.TRANSFER:
            return f"Transfer to {receiver_username}"
        return self.type.value.capitalize()


class DepositRequest(CamelModel):
    amount: float = Field(gt=0)
    description: str | None = None


class TransactionOut(CamelModel):
    id: str
    transaction_id: str
    type: TransactionType
    description: str
    category: str
    amount: float  # always positive; `direction` carries the sign
    direction: TransactionDirection
    status: TransactionStatus
    sender_username: str
    receiver_username: str
    occurred_at: UtcDateTime


class TransferRecipientOut(CamelModel):
    id: str
    username: str
    name: str
    city: str
    country: str
    profile_picture: str | None = None