"""Bank service catalogue and company listings."""

from httpx import AsyncClient
from sqlalchemy import select

from app.models.bank_service import BankService, BankServiceStatus
from app.models.company import Company
from tests.conftest import login, register

SERVICES = [
    ("High-Yield Savings", "4.2% APY, no monthly fee.", "Savings", 120),
    ("Everyday Checking", "Unlimited transfers.", "Checking", 300),
    ("Life Insurance", "Whole-life policy.", "Insurance", 40),
    ("Travel Rewards", "3x travel points.", "Cards", 210),
]

COMPANIES = [
    ("Apple Inc.", "AAPL", "Technology", 227.4, 1.82, True),
    ("Tesla Inc.", "TSLA", "Automotive", 248.5, -2.61, True),
    ("JPMorgan Chase", "JPM", "Financial Services", 218.7, 0.34, False),
]


async def _catalogue(client: AsyncClient, session_factory) -> None:
    """Sign in and seed the service/company catalogue."""
    await register(client)
    await login(client)
    async with session_factory() as db:
        db.add_all(
            BankService(
                name=n, details=d, type=t,
                status=BankServiceStatus.ACTIVE, number_of_users=c,
            )
            for n, d, t, c in SERVICES
        )
        db.add_all(
            Company(name=n, symbol=s, sector=sec, price=p, change_percent=c, is_trending=t)
            for n, s, sec, p, c, t in COMPANIES
        )
        await db.commit()
    return None


async def test_services_are_listed_and_paged(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    page = (await client.get("/api/v1/bank-services")).json()["data"]

    assert page["totalItems"] == 4
    assert [s["name"] for s in page["items"]] == sorted(s[0] for s in SERVICES)
    assert all(s["status"] == "ACTIVE" for s in page["items"])
    assert all(isinstance(s["numberOfUsers"], int) for s in page["items"])


async def test_services_can_be_filtered_and_searched(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    insurance = (
        await client.get("/api/v1/bank-services", params={"type": "Insurance"})
    ).json()["data"]
    assert insurance["totalItems"] == 1
    assert insurance["items"][0]["name"] == "Life Insurance"

    found = (
        await client.get("/api/v1/bank-services/search", params={"q": "points"})
    ).json()["data"]
    assert [s["name"] for s in found] == ["Travel Rewards"]

    by_name = (
        await client.get("/api/v1/bank-services", params={"search": "savings"})
    ).json()["data"]
    assert by_name["totalItems"] == 1


async def test_service_detail_and_admin_mutations(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    page = (await client.get("/api/v1/bank-services")).json()["data"]
    service_id = page["items"][0]["id"]

    assert (
        await client.get(f"/api/v1/bank-services/{service_id}")
    ).status_code == 200

    # A plain user cannot modify the catalogue.
    assert (
        await client.put(
            f"/api/v1/bank-services/{service_id}", json={"details": "hacked"}
        )
    ).status_code == 403
    assert (
        await client.delete(f"/api/v1/bank-services/{service_id}")
    ).status_code == 403


async def test_companies_are_listed(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    page = (await client.get("/api/v1/companies")).json()["data"]

    assert page["totalItems"] == 3
    assert [c["symbol"] for c in page["items"]] == ["AAPL", "JPM", "TSLA"]


async def test_trending_companies_are_filtered_and_ranked(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    trending = (
        await client.get("/api/v1/companies/trending")
    ).json()["data"]

    assert {c["symbol"] for c in trending} == {"AAPL", "TSLA"}
    # Ranked by best day change first.
    assert [c["changePercent"] for c in trending] == [1.82, -2.61]


async def test_catalogue_requires_authentication(client: AsyncClient):
    assert (await client.get("/api/v1/bank-services")).status_code == 401
    assert (await client.get("/api/v1/companies")).status_code == 401


async def test_health_is_public(client: AsyncClient):
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "up"


async def test_unknown_service_is_a_404(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    assert (
        await client.get("/api/v1/bank-services/nope")
    ).status_code == 404


async def test_search_requires_a_query(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    assert (
        await client.get("/api/v1/bank-services/search")
    ).status_code == 422


async def test_service_name_filter_is_case_insensitive(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    page = (
        await client.get("/api/v1/bank-services", params={"search": "SAVINGS"})
    ).json()["data"]

    assert page["totalItems"] == 1


async def test_company_names_are_unique(client: AsyncClient, session_factory):
    await _catalogue(client, session_factory)

    from app.core.errors import ConflictError
    from app.schemas.company import CreateCompanyRequest
    from app.services.company import create_company

    async with session_factory() as db:
        try:
            await create_company(db, None, CreateCompanyRequest(name="Apple Inc.", symbol="X"))
        except ConflictError as exc:
            assert "already exists" in exc.message
        else:
            raise AssertionError("expected a ConflictError")

    # Nothing was written.
    async with session_factory() as db:
        assert len((await db.scalars(select(Company))).all()) == 3