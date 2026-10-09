"""User, preference, and dashboard-summary schemas."""

from datetime import date

from pydantic import EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.common import CamelModel, UtcDateTime


class PreferencesRequest(CamelModel):
    currency: str = Field(default="USD", max_length=8)
    time_zone: str = Field(default="GMT-5", max_length=64)
    sent_or_receive_digital_currency: bool = False
    receive_merchant_order: bool = False
    account_recommendations: bool = False
    two_factor_authentication: bool = False


class PreferencesOut(CamelModel):
    currency: str
    time_zone: str
    sent_or_receive_digital_currency: bool
    receive_merchant_order: bool
    account_recommendations: bool
    two_factor_authentication: bool


#: Update uses the same shape; every field is defaulted so a partial body works.
UpdatePreferencesRequest = PreferencesRequest


class RegisterRequest(CamelModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    username: str = Field(min_length=3, max_length=60)
    password: str = Field(min_length=8, max_length=128)
    date_of_birth: date
    permanent_address: str = Field(min_length=1, max_length=255)
    present_address: str = Field(min_length=1, max_length=255)
    postal_code: str = Field(min_length=1, max_length=20)
    city: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    profile_picture: str | None = None
    preferences: PreferencesRequest = Field(default_factory=PreferencesRequest)

    @field_validator("username")
    @classmethod
    def normalise_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.replace("_", "").replace(".", "").replace("-", "").isalnum():
            raise ValueError("username may only contain letters, numbers, and _ . -")
        return v


class UpdateProfileRequest(CamelModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    permanent_address: str | None = Field(default=None, max_length=255)
    present_address: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    profile_picture: str | None = None


class UserOut(CamelModel):
    id: str
    name: str
    username: str
    email: str
    date_of_birth: date
    permanent_address: str
    present_address: str
    city: str
    country: str
    postal_code: str
    profile_picture: str | None = None
    role: UserRole
    account_balance: float
    created_at: UtcDateTime
    preferences: PreferencesOut | None = None


class PublicUserOut(CamelModel):
    """Safe projection for other people's profiles - no email, no balance."""

    id: str
    name: str
    username: str
    city: str
    country: str
    profile_picture: str | None = None


class AccountSummaryOut(CamelModel):
    account_balance: float
    total_income: float
    total_expense: float
    total_savings: float


class CategoryTotal(CamelModel):
    """Total spend in one category over a window."""

    category: str
    total: float


class SeriesPoint(CamelModel):
    """A labelled point on a time series. ``period`` is ``YYYY-MM`` or ``YYYY``."""

    period: str
    value: float


class InvestmentSummaryOut(CamelModel):
    total_investment: float
    rate_of_return: float
    number_of_investments: int
    yearly_investments: list[SeriesPoint]
    monthly_revenue: list[SeriesPoint]