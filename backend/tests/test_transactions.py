"""Ledger behaviour: transfers, deposits, balances, pagination, series."""

from httpx import AsyncClient

from tests.conftest import auth_headers, login, register


async def _two_accounts(client: AsyncClient) -> tuple[dict, dict]:
    """Register and sign in two users, each as ``{tokens, headers}``."""
    await register(client)
    await register(
        client,
        name="Alice Nguyen",
        email="alice@bankdash.dev",
        username="alice",
    )

    def wrap(tokens: dict) -> dict:
        return {"tokens": tokens, "headers": auth_headers(tokens)}

    return wrap(await login(client)), wrap(await login(client, username="alice"))


async def _fund(client: AsyncClient, headers: dict, amount: float = 1_000.0) -> dict:
    response = await client.post(
        "/api/v1/transactions/deposit", json={"amount": amount}, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def test_transfer_moves_money_and_writes_both_legs(client: AsyncClient):
    sender, receiver = await _two_accounts(client)
    await _fund(client, sender["headers"], 1_000.0)

    response = await client.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 250.0, "receiverUsername": "alice"},
        headers=sender["headers"],
    )
    assert response.status_code == 201, response.text
    outgoing = response.json()["data"]

    assert outgoing["amount"] == 250.0
    assert outgoing["direction"] == "OUT"
    assert outgoing["transactionId"].startswith("TXN-")
    assert outgoing["receiverUsername"] == "alice"

    # The receiver has a matching IN leg.
    received = await client.get(
        "/api/v1/transactions", params={"page": 0, "size": 5}, headers=receiver["headers"]
    )
    leg = received.json()["data"]["items"][0]
    assert leg["direction"] == "IN"
    assert leg["amount"] == 250.0
    assert leg["senderUsername"] == "tester"
    assert leg["receiverUsername"] == "alice"

    # Balances reflect the movement.
    sender_me = (await client.get("/api/v1/users/me", headers=sender["headers"])).json()["data"]
    receiver_me = (
        await client.get("/api/v1/users/me", headers=receiver["headers"])
    ).json()["data"]
    assert sender_me["accountBalance"] == 750.0
    assert receiver_me["accountBalance"] == 250.0


async def test_transfer_is_rejected_when_funds_are_insufficient(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 100.0)

    response = await client.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 500.0, "receiverUsername": "alice"},
        headers=sender["headers"],
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Insufficient funds"
    assert response.json()["data"]["code"] == "insufficient_funds"

    # Balance untouched.
    me = (await client.get("/api/v1/users/me", headers=sender["headers"])).json()["data"]
    assert me["accountBalance"] == 100.0


async def test_transfer_to_an_unknown_user_is_a_404(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 500.0)

    response = await client.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 10.0, "receiverUsername": "nobody"},
        headers=sender["headers"],
    )

    assert response.status_code == 404


async def test_transfer_to_self_is_rejected(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 500.0)

    response = await client.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 10.0, "receiverUsername": "tester"},
        headers=sender["headers"],
    )

    assert response.status_code == 400
    assert "yourself" in response.json()["message"]


async def test_transfer_without_a_receiver_is_rejected(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 500.0)

    response = await client.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 10.0},
        headers=sender["headers"],
    )

    assert response.status_code == 400
    assert "receiverUsername" in response.json()["message"]


async def test_shopping_needs_no_counterparty_and_is_an_outflow(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 500.0)

    response = await client.post(
        "/api/v1/transactions",
        json={"type": "shopping", "amount": 40.0, "description": "Groceries"},
        headers=sender["headers"],
    )

    assert response.status_code == 201, response.text
    body = response.json()["data"]
    assert body["direction"] == "OUT"
    assert body["receiverUsername"] == "BankDash"
    assert body["description"] == "Groceries"


async def test_incomes_and_expenses_split_by_direction(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 1_000.0)
    await client.post(
        "/api/v1/transactions",
        json={"type": "shopping", "amount": 100.0},
        headers=sender["headers"],
    )
    await client.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 200.0, "receiverUsername": "alice"},
        headers=sender["headers"],
    )

    everything = (
        await client.get("/api/v1/transactions", headers=sender["headers"])
    ).json()["data"]
    incomes = (
        await client.get("/api/v1/transactions/incomes", headers=sender["headers"])
    ).json()["data"]
    expenses = (
        await client.get("/api/v1/transactions/expenses", headers=sender["headers"])
    ).json()["data"]

    assert everything["totalItems"] == 3
    assert incomes["totalItems"] == 1
    assert all(i["direction"] == "IN" for i in incomes["items"])
    assert expenses["totalItems"] == 2
    assert all(e["direction"] == "OUT" for e in expenses["items"])


async def test_pagination_is_zero_indexed_and_consistent(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 500.0)
    for index in range(7):
        await client.post(
            "/api/v1/transactions",
            json={"type": "shopping", "amount": float(index + 1)},
            headers=sender["headers"],
        )

    first = (
        await client.get(
            "/api/v1/transactions", params={"page": 0, "size": 3}, headers=sender["headers"]
        )
    ).json()["data"]
    second = (
        await client.get(
            "/api/v1/transactions", params={"page": 1, "size": 3}, headers=sender["headers"]
        )
    ).json()["data"]
    third = (
        await client.get(
            "/api/v1/transactions", params={"page": 2, "size": 3}, headers=sender["headers"]
        )
    ).json()["data"]

    assert first["totalItems"] == 8
    assert first["totalPages"] == 3
    assert first["hasNext"] is True
    assert first["hasPrevious"] is False
    assert second["hasNext"] is True and second["hasPrevious"] is True
    assert third["hasNext"] is False and len(third["items"]) == 2

    # Pages must not overlap.
    seen = [i["id"] for page in (first, second, third) for i in page["items"]]
    assert len(set(seen)) == 8


async def test_timestamps_serialise_as_utc_iso(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 100.0)

    items = (
        await client.get("/api/v1/transactions", headers=sender["headers"])
    ).json()["data"]["items"]

    assert items[0]["occurredAt"].endswith("Z")


async def test_balance_history_reconstructs_history(client: AsyncClient):
    sender, _ = await _two_accounts(client)
    await _fund(client, sender["headers"], 1_000.0)
    await client.post(
        "/api/v1/transactions",
        json={"type": "shopping", "amount": 400.0},
        headers=sender["headers"],
    )

    points = (
        await client.get(
            "/api/v1/transactions/balance-history", params={"months": 6}, headers=sender["headers"]
        )
    ).json()["data"]

    assert len(points) == 6
    assert points[-1]["value"] == 600.0  # current balance is the final point
    # Both movements happened this month, so the account was still empty at the
    # start of it - every earlier point must therefore be 0.
    assert all(p["value"] == 0.0 for p in points[:-1])


async def test_transfer_recipients_lists_other_users(client: AsyncClient):
    sender, receiver = await _two_accounts(client)
    await register(client, name="Bob", email="bob@bankdash.dev", username="bob")

    recipients = (
        await client.get(
            "/api/v1/transactions/transfer-recipients", headers=sender["headers"]
        )
    ).json()["data"]

    names = {r["username"] for r in recipients}
    assert "tester" not in names  # never suggest yourself
    assert {"alice", "bob"} <= names


async def test_get_transaction_by_id_and_isolation(client: AsyncClient):
    sender, receiver = await _two_accounts(client)
    await _fund(client, sender["headers"], 1_000.0)
    created = await client.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 25.0, "receiverUsername": "alice"},
        headers=sender["headers"],
    )
    txn_id = created.json()["data"]["id"]

    own = await client.get(f"/api/v1/transactions/{txn_id}", headers=sender["headers"])
    assert own.status_code == 200

    # Alice holds her own leg under a different id, so the sender's row must not
    # be readable by anyone else.
    assert (
        await client.get(f"/api/v1/transactions/{txn_id}", headers=receiver["headers"])
    ).status_code == 404

    assert (
        await client.get("/api/v1/transactions/does-not-exist", headers=sender["headers"])
    ).status_code == 404


async def test_amount_must_be_positive(client: AsyncClient):
    sender, _ = await _two_accounts(client)

    response = await client.post(
        "/api/v1/transactions",
        json={"type": "shopping", "amount": -5},
        headers=sender["headers"],
    )

    assert response.status_code == 422
    assert response.json()["success"] is False