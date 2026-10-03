"""Profile, preferences, summaries, and the investment series."""

from httpx import AsyncClient

from tests.conftest import auth_headers, login, register


async def test_me_returns_the_full_profile(client: AsyncClient):
    await register(client)
    await login(client)

    body = (await client.get("/api/v1/users/me")).json()

    assert body["success"] is True
    assert body["message"] is None
    assert body["data"]["username"] == "tester"
    assert body["data"]["dateOfBirth"] == "1990-04-12"
    assert body["data"]["preferences"]["currency"] == "USD"


async def test_update_profile(client: AsyncClient):
    await register(client)
    await login(client)

    response = await client.put(
        "/api/v1/users/me",
        json={"name": "Renamed User", "city": "Boston"},
    )
    assert response.status_code == 200

    body = (await client.get("/api/v1/users/me")).json()["data"]
    assert body["name"] == "Renamed User"
    assert body["city"] == "Boston"
    # Untouched fields survive a partial update.
    assert body["email"] == "test@bankdash.dev"


async def test_update_profile_rejects_an_email_already_in_use(client: AsyncClient):
    await register(client)
    await register(client, username="alice", email="alice@bankdash.dev")
    await login(client)

    response = await client.put(
        "/api/v1/users/me", json={"email": "alice@bankdash.dev"}
    )

    assert response.status_code == 409


async def test_update_preferences_round_trips(client: AsyncClient):
    await register(client)
    await login(client)

    response = await client.put(
        "/api/v1/users/me/preferences",
        json={
            "currency": "EUR",
            "timeZone": "GMT+1",
            "sentOrReceiveDigitalCurrency": True,
            "twoFactorAuthentication": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["currency"] == "EUR"

    me = (await client.get("/api/v1/users/me")).json()["data"]
    assert me["preferences"]["currency"] == "EUR"
    assert me["preferences"]["timeZone"] == "GMT+1"
    assert me["preferences"]["twoFactorAuthentication"] is True
    # Fields not supplied keep their previous value.
    assert me["preferences"]["receiveMerchantOrder"] is False


async def test_summary_reflects_movements(client: AsyncClient):
    await register(client)
    await login(client)

    await client.post(
        "/api/v1/transactions/deposit", json={"amount": 900.0}
    )
    await client.post(
        "/api/v1/transactions", json={"type": "shopping", "amount": 250.0}
    )

    summary = (await client.get("/api/v1/users/me/summary")).json()["data"]

    assert summary["accountBalance"] == 650.0
    assert summary["totalIncome"] == 900.0
    assert summary["totalExpense"] == 250.0
    assert summary["totalSavings"] == 650.0


async def test_investment_summary_shape_and_stability(client: AsyncClient):
    await register(client)
    await login(client)

    response = await client.get(
        "/api/v1/users/me/investment-summary",
        params={"years": 4, "months": 6},
    )
    assert response.status_code == 200
    body = response.json()["data"]

    assert isinstance(body["totalInvestment"], float)
    assert isinstance(body["rateOfReturn"], float)
    assert isinstance(body["numberOfInvestments"], int)
    assert len(body["yearlyInvestments"]) == 4
    assert len(body["monthlyRevenue"]) == 6
    assert all("period" in p and "value" in p for p in body["monthlyRevenue"])

    # Deterministic per user: a second call returns identical figures.
    again = (
        await client.get(
            "/api/v1/users/me/investment-summary",
            params={"years": 4, "months": 6},
        )
    ).json()["data"]
    assert again == body


async def test_public_profile_hides_private_fields(client: AsyncClient):
    await register(client)
    await register(client, username="alice", email="alice@bankdash.dev")

    body = (
        await client.get("/api/v1/users/alice", headers=auth_headers(await login(client)))
    ).json()["data"]

    assert body["username"] == "alice"
    assert body["name"] == "Test User"
    assert "email" not in body
    assert "accountBalance" not in body


async def test_unknown_public_profile_is_a_404(client: AsyncClient):
    await register(client)
    await login(client)

    assert (await client.get("/api/v1/users/ghost")).status_code == 404


async def test_validation_errors_use_the_envelope(client: AsyncClient):
    await register(client)
    await login(client)

    response = await client.put(
        "/api/v1/users/me", json={"email": "not-an-email"}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"]["code"] == "validation_error"
    assert "email" in body["message"]
