"""Loan schemas."""

from datetime import date

from pydantic import Field

from app.models.loan import LoanStatus, LoanType
from app.schemas.common import CamelModel, UtcDateTime


class CreateLoanRequest(CamelModel):
    loan_type: LoanType
    loan_amount: float = Field(gt=0)
    loan_duration: int = Field(gt=0, le=600)  # months
    interest_rate: float = Field(ge=0, le=100)


class RepayLoanRequest(CamelModel):
    #: Omit to repay the full outstanding amount.
    amount: float | None = Field(default=None, gt=0)


class LoanOut(CamelModel):
    id: str
    loan_type: LoanType
    loan_amount: float
    amount_left_to_repay: float
    installment: float
    interest_rate: float
    loan_duration: int
    status: LoanStatus
    start_date: date | None = None
    end_date: date | None = None
    created_at: UtcDateTime


class LoanSummaryOut(CamelModel):
    personal_loan: float
    corporate_loan: float
    business_loan: float
    total_outstanding: float


class RepayResultOut(CamelModel):
    loan: LoanOut
    amount_paid: float