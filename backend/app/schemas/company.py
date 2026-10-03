"""Company schemas."""

from pydantic import Field

from app.schemas.common import CamelModel


class CreateCompanyRequest(CamelModel):
    name: str = Field(min_length=1, max_length=120)
    symbol: str = Field(min_length=1, max_length=12)
    sector: str = ""
    price: float = Field(default=0.0, ge=0)
    change_percent: float = 0.0
    logo_url: str | None = None
    is_trending: bool = False


class UpdateCompanyRequest(CamelModel):
    name: str | None = Field(default=None, max_length=120)
    symbol: str | None = Field(default=None, max_length=12)
    sector: str | None = None
    price: float | None = Field(default=None, ge=0)
    change_percent: float | None = None
    logo_url: str | None = None
    is_trending: bool | None = None


class CompanyOut(CamelModel):
    id: str
    name: str
    symbol: str
    sector: str
    price: float
    change_percent: float
    logo_url: str | None = None
    is_trending: bool