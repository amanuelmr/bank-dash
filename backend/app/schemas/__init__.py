"""Re-export every response/request schema for convenient importing.

Deliberately excludes `TokenPair`: it is the internal return type of the auth
service, not part of the wire contract. No route takes or returns it, and it is
absent from the published OpenAPI schemas - re-exporting it here would imply
otherwise to anyone reading the API surface.
"""

from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
)
from app.schemas.bank_service import (
    BankServiceOut,
    CreateBankServiceRequest,
    UpdateBankServiceRequest,
)
from app.schemas.card import CardOut, CreateCardRequest
from app.schemas.common import ApiResponse, CamelModel, Page, UtcDateTime
from app.schemas.company import CompanyOut, CreateCompanyRequest, UpdateCompanyRequest
from app.schemas.loan import (
    CreateLoanRequest,
    LoanOut,
    LoanSummaryOut,
    RepayLoanRequest,
    RepayResultOut,
)
from app.schemas.transaction import (
    CreateTransactionRequest,
    DepositRequest,
    TransactionOut,
    TransferRecipientOut,
)
from app.schemas.user import (
    AccountSummaryOut,
    InvestmentSummaryOut,
    PreferencesOut,
    PreferencesRequest,
    PublicUserOut,
    RegisterRequest,
    SeriesPoint,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
    UserOut,
)

__all__ = [
    "AccountSummaryOut",
    "ApiResponse",
    "BankServiceOut",
    "CamelModel",
    "CardOut",
    "ChangePasswordRequest",
    "CompanyOut",
    "CreateBankServiceRequest",
    "CreateCardRequest",
    "CreateCompanyRequest",
    "CreateLoanRequest",
    "CreateTransactionRequest",
    "DepositRequest",
    "InvestmentSummaryOut",
    "LoanOut",
    "LoanSummaryOut",
    "LoginRequest",
    "Page",
    "PreferencesOut",
    "PreferencesRequest",
    "PublicUserOut",
    "RefreshRequest",
    "RegisterRequest",
    "RepayLoanRequest",
    "RepayResultOut",
    "SeriesPoint",
    "TransactionOut",
    "TransferRecipientOut",
    "UpdateBankServiceRequest",
    "UpdateCompanyRequest",
    "UpdatePreferencesRequest",
    "UpdateProfileRequest",
    "UserOut",
    "UtcDateTime",
]