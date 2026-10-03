"""Card issuing, listing, and deletion."""

from httpx import AsyncClient

from tests.conftest import login, register

NEW_CARD = {
    "cardType": "Platinum",
    "cardHolder": "Test User",
    "balance": 2_500.0,
    "expiryDate": "2029-04-30",
    "passcode": "4821",
}


async def test_list_cards_is_empty_for_a_new_account(client: AsyncClient):
    await register(client)
    await login(client)

    page = (await client.get("/api/v1/cards")).json()["data"]

    assert page["items"] == []
    assert page["totalItems"] == 0
    assert page["totalPages"] == 0
    assert page["hasNext"] is False


async def test_create_card_never_exposes_a_full_number(client: AsyncClient):
    await register(client)
    await login(client)

    response = await client.post("/api/v1/cards", json=NEW_CARD)
    assert response.status_code == 201
    card = response.json()["data"]

    assert card["cardType"] == "Platinum"
    assert card["cardHolder"] == "Test User"
    assert card["balance"] == 2_500.0
    # A plain date, not an ISO datetime - the UI formats it directly.
    assert card["expiryDate"] == "2029-04-30"
    assert card["status"] == "ACTIVE"
    assert card["maskedNumber"].startswith("****")
    assert len(card["maskedNumber"]) == 19

    # Nothing resembling a real PAN is present.
    serialised = response.text.replace(" ", "")
    assert "4821" not in serialised or "masked" in card


async def test_cards_are_listed_and_scoped_to_their_owner(client_factory):
    # Cookie auth means each identity needs its own client/jar.
    tester = await client_factory()
    alice = await client_factory()
    await register(tester)
    await login(tester)
    await register(alice, username="alice", email="alice@bankdash.dev")
    await login(alice, username="alice")

    await tester.post("/api/v1/cards", json=NEW_CARD)
    await alice.post(
        "/api/v1/cards", json={**NEW_CARD, "cardHolder": "Alice Nguyen"}
    )

    mine = (await tester.get("/api/v1/cards")).json()["data"]
    theirs = (await alice.get("/api/v1/cards")).json()["data"]

    assert mine["totalItems"] == 1
    assert mine["items"][0]["cardHolder"] == "Test User"
    assert theirs["totalItems"] == 1
    assert theirs["items"][0]["cardHolder"] == "Alice Nguyen"


async def test_card_is_ordered_newest_first(client: AsyncClient):
    await register(client)
    await login(client)

    for holder in ("First", "Second", "Third"):
        await client.post(
            "/api/v1/cards", json={**NEW_CARD, "cardHolder": holder}
        )

    items = (await client.get("/api/v1/cards")).json()["data"]["items"]
    assert [c["cardHolder"] for c in items] == ["Third", "Second", "First"]


async def test_get_and_delete_card(client: AsyncClient):
    await register(client)
    await login(client)
    created = (await client.post("/api/v1/cards", json=NEW_CARD)).json()["data"]

    assert (
        await client.get(f"/api/v1/cards/{created['id']}")
    ).status_code == 200
    assert (
        await client.delete(f"/api/v1/cards/{created['id']}")
    ).status_code == 200
    assert (
        await client.get(f"/api/v1/cards/{created['id']}")
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/cards/{created['id']}")
    ).status_code == 404


async def test_card_requires_authentication(client: AsyncClient):
    assert (await client.get("/api/v1/cards")).status_code == 401


async def test_card_validates_its_input(client: AsyncClient):
    await register(client)
    await login(client)

    bad_passcode = await client.post(
        "/api/v1/cards", json={**NEW_CARD, "passcode": "1"}
    )
    assert bad_passcode.status_code == 422

    bad_balance = await client.post(
        "/api/v1/cards", json={**NEW_CARD, "balance": -10}
    )
    assert bad_balance.status_code == 422