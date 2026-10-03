"""Bank service schemas."""

from pydantic import Field

from app.models.bank_service import BankServiceStatus
from app.schemas.common import CamelModel


class CreateBankServiceRequest(CamelModel):
    name: str = Field(min_length=1, max_length=120)
    details: str = ""
    type: str = Field(min_length=1, max_length=60)
    status: BankServiceStatus = BankServiceStatus.ACTIVE
    number_of_users: int = Field(default=0, ge=0)


class UpdateBankServiceRequest(CamelModel):
    name: str | None = Field(default=None, max_length=120)
    details: str | None = None
    type: str | None = Field(default=None, max_length=60)
    status: BankServiceStatus | None = None
    number_of_users: int | None = Field(default=None, ge=0)


class BankServiceOut(CamelModel):
    id: str
    name: str
    details: str
    type: str
    status: BankServiceStatus
    number_of_users: int