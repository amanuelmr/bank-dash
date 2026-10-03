"""Loan application, approval, repayment, and summary totals."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.loan import Loan, LoanStatus
from app.models.user import User, UserRole
from tests.conftest import auth_headers, login, register

APPLICATION = {
    "loanType": "Personal Loan",
    "loanAmount": 6_000.0,
    "loanDuration": 12,
    "interestRate": 8.0,
}


async def _borrower(client: AsyncClient, username: str = "tester") -> dict:
    await register(client, username=username, email=f"{username}@bankdash.dev")
    return auth_headers(await login(client, username=username))


async def _promote(session_factory, username: str = "tester") -> None:
    async with session_factory() as db:
        user = await db.scalar(select(User).where(User.username == username))
        user.role = UserRole.ADMIN
        await db.commit()


async def _activate(session_factory, loan_id: str) -> None:
    """Move a loan out of PENDING so it becomes repayable."""
    async with session_factory() as db:
        loan = await db.scalar(select(Loan).where(Loan.id == loan_id))
        loan.status = LoanStatus.ACTIVE
        await db.commit()


async def test_apply_for_a_loan_computes_an_amortised_installment(client: AsyncClient):
    headers = await _borrower(client)

    response = await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    assert response.status_code == 201
    loan = response.json()["data"]

    assert loan["loanAmount"] == 6_000.0
    assert loan["amountLeftToRepay"] == 6_000.0
    assert loan["status"] == "PENDING"
    assert loan["loanDuration"] == 12
    # 6,000 over 12 months at 8%/yr is 521.93/month by standard amortisation.
    assert loan["installment"] == pytest.approx(521.93, abs=0.01)
    assert loan["installment"] * loan["loanDuration"] > loan["loanAmount"]


async def test_loans_are_scoped_to_their_owner(client: AsyncClient):
    alice = await _borrower(client)
    await _borrower(client, "bob")
    bob = auth_headers(await login(client, username="bob"))

    await client.post("/api/v1/loans", json=APPLICATION, headers=alice)

    assert (await client.get("/api/v1/loans", headers=alice)).json()["data"]["totalItems"] == 1
    assert (await client.get("/api/v1/loans", headers=bob)).json()["data"]["totalItems"] == 0


async def test_a_plain_user_cannot_approve(client: AsyncClient):
    headers = await _borrower(client)
    loan = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]

    assert (
        await client.post(f"/api/v1/loans/{loan['id']}/approve", headers=headers)
    ).status_code == 403
    assert (await client.get("/api/v1/loans/all", headers=headers)).status_code == 403


async def test_admin_can_approve(client: AsyncClient, session_factory):
    headers = await _borrower(client)
    loan = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]

    await _promote(session_factory)

    approved = await client.post(f"/api/v1/loans/{loan['id']}/approve", headers=headers)
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "ACTIVE"
    assert approved.json()["data"]["startDate"] is not None

    # Only pending loans can be decided.
    assert (
        await client.post(f"/api/v1/loans/{loan['id']}/approve", headers=headers)
    ).status_code == 400


async def test_admin_can_reject(client: AsyncClient, session_factory):
    headers = await _borrower(client)
    loan = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]

    await _promote(session_factory)
    rejected = await client.post(f"/api/v1/loans/{loan['id']}/reject", headers=headers)

    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "REJECTED"


async def test_summary_counts_only_active_loans(client: AsyncClient, session_factory):
    headers = await _borrower(client)
    personal = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]
    business = (
        await client.post(
            "/api/v1/loans",
            json={**APPLICATION, "loanType": "Business Loan", "loanAmount": 12_000.0},
            headers=headers,
        )
    ).json()["data"]

    # Pending loans are not yet outstanding.
    pending = (await client.get("/api/v1/loans/summary", headers=headers)).json()["data"]
    assert pending["totalOutstanding"] == 0.0
    assert pending["personalLoan"] == 0.0

    async with session_factory() as db:
        for loan_id in (personal["id"], business["id"]):
            loan = await db.scalar(select(Loan).where(Loan.id == loan_id))
            loan.status = LoanStatus.ACTIVE
        await db.commit()

    summary = (await client.get("/api/v1/loans/summary", headers=headers)).json()["data"]
    assert summary["personalLoan"] == 6_000.0
    assert summary["businessLoan"] == 12_000.0
    assert summary["corporateLoan"] == 0.0
    assert summary["totalOutstanding"] == 18_000.0


async def test_repayment_debits_the_account(client: AsyncClient, session_factory):
    headers = await _borrower(client)
    await client.post(
        "/api/v1/transactions/deposit", json={"amount": 2_000.0}, headers=headers
    )
    loan = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]
    await _activate(session_factory, loan["id"])

    response = await client.post(
        f"/api/v1/loans/{loan['id']}/repay", json={"amount": 2_000.0}, headers=headers
    )
    assert response.status_code == 200
    body = response.json()["data"]

    assert body["amountPaid"] == 2_000.0
    assert body["loan"]["amountLeftToRepay"] == 4_000.0
    assert body["loan"]["status"] == "ACTIVE"

    me = (await client.get("/api/v1/users/me", headers=headers)).json()["data"]
    assert me["accountBalance"] == 0.0

    # The repayment also appears as an outflow on the statement.
    items = (await client.get("/api/v1/transactions/expenses", headers=headers)).json()["data"]
    assert items["items"][0]["type"] == "loan_repayment"
    assert items["items"][0]["amount"] == 2_000.0


async def test_omitting_the_amount_clears_the_whole_loan(client: AsyncClient, session_factory):
    headers = await _borrower(client)
    await client.post(
        "/api/v1/transactions/deposit", json={"amount": 20_000.0}, headers=headers
    )
    loan = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]
    await _activate(session_factory, loan["id"])

    body = (await client.post(f"/api/v1/loans/{loan['id']}/repay", headers=headers)).json()["data"]

    assert body["amountPaid"] == 6_000.0
    assert body["loan"]["amountLeftToRepay"] == 0.0
    assert body["loan"]["status"] == "PAID"


async def test_overpayment_is_clamped_to_the_outstanding_amount(
    client: AsyncClient, session_factory
):
    headers = await _borrower(client)
    await client.post(
        "/api/v1/transactions/deposit", json={"amount": 20_000.0}, headers=headers
    )
    loan = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]
    await _activate(session_factory, loan["id"])

    body = (
        await client.post(
            f"/api/v1/loans/{loan['id']}/repay", json={"amount": 99_999.0}, headers=headers
        )
    ).json()["data"]

    assert body["amountPaid"] == 6_000.0
    assert body["loan"]["status"] == "PAID"
    me = (await client.get("/api/v1/users/me", headers=headers)).json()["data"]
    assert me["accountBalance"] == 14_000.0


async def test_repayment_beyond_the_balance_is_rejected(client: AsyncClient, session_factory):
    headers = await _borrower(client)
    loan = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]
    await _activate(session_factory, loan["id"])

    response = await client.post(f"/api/v1/loans/{loan['id']}/repay", headers=headers)

    assert response.status_code == 400
    assert response.json()["data"]["code"] == "insufficient_funds"


async def test_a_rejected_loan_cannot_be_repaid(client: AsyncClient, session_factory):
    headers = await _borrower(client)
    await client.post(
        "/api/v1/transactions/deposit", json={"amount": 20_000.0}, headers=headers
    )
    loan = (
        await client.post("/api/v1/loans", json=APPLICATION, headers=headers)
    ).json()["data"]

    async with session_factory() as db:
        row = await db.scalar(select(Loan).where(Loan.id == loan["id"]))
        row.status = LoanStatus.REJECTED
        await db.commit()

    response = await client.post(f"/api/v1/loans/{loan['id']}/repay", headers=headers)
    assert response.status_code == 400
    assert "not currently repayable" in response.json()["message"]


async def test_cannot_repay_someone_elses_loan(client: AsyncClient, session_factory):
    alice = await _borrower(client)
    await _borrower(client, "bob")
    bob = auth_headers(await login(client, username="bob"))
    await client.post(
        "/api/v1/transactions/deposit", json={"amount": 20_000.0}, headers=bob
    )

    loan = (await client.post("/api/v1/loans", json=APPLICATION, headers=alice)).json()["data"]
    await _activate(session_factory, loan["id"])

    assert (await client.post(f"/api/v1/loans/{loan['id']}/repay", headers=bob)).status_code == 404
    assert (await client.get(f"/api/v1/loans/{loan['id']}", headers=bob)).status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {**APPLICATION, "loanAmount": 0},
        {**APPLICATION, "loanDuration": 0},
        {**APPLICATION, "interestRate": 150},
        {**APPLICATION, "loanType": "Spaceship Loan"},
    ],
)
async def test_loan_input_is_validated(client: AsyncClient, payload: dict):
    headers = await _borrower(client)
    assert (await client.post("/api/v1/loans", json=payload, headers=headers)).status_code == 422


async def test_loan_endpoints_require_authentication(client: AsyncClient):
    assert (await client.get("/api/v1/loans")).status_code == 401
    assert (await client.get("/api/v1/loans/summary")).status_code == 401