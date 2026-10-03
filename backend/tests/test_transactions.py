"""Ledger behaviour: transfers, deposits, balances, pagination, series."""

from httpx import AsyncClient

from tests.conftest import login, register


async def _two_accounts(client_factory) -> tuple[AsyncClient, AsyncClient]:
    """Two signed-in users.

    Auth is cookie based and a cookie jar belongs to one client, so each user
    needs their own client rather than a shared one.
    """
    sender = await client_factory()
    receiver = await client_factory()

    await register(sender)
    await register(
        receiver,
        name="Alice Nguyen",
        email="alice@bankdash.dev",
        username="alice",
    )
    await login(sender)
    await login(receiver, username="alice")
    return sender, receiver


async def _fund(client: AsyncClient, amount: float = 1_000.0) -> dict:
    response = await client.post("/api/v1/transactions/deposit", json={"amount": amount})
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def test_transfer_moves_money_and_writes_both_legs(client_factory):
    sender, receiver = await _two_accounts(client_factory)
    await _fund(sender, 1_000.0)

    response = await sender.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 250.0, "receiverUsername": "alice"},
    )
    assert response.status_code == 201, response.text
    outgoing = response.json()["data"]

    assert outgoing["amount"] == 250.0
    assert outgoing["direction"] == "OUT"
    assert outgoing["transactionId"].startswith("TXN-")
    assert outgoing["receiverUsername"] == "alice"

    # The receiver has a matching IN leg.
    received = await receiver.get(
        "/api/v1/transactions", params={"page": 0, "size": 5}
    )
    leg = received.json()["data"]["items"][0]
    assert leg["direction"] == "IN"
    assert leg["amount"] == 250.0
    assert leg["senderUsername"] == "tester"
    assert leg["receiverUsername"] == "alice"

    # Balances reflect the movement.
    sender_me = (await sender.get("/api/v1/users/me")).json()["data"]
    receiver_me = (await receiver.get("/api/v1/users/me")).json()["data"]
    assert sender_me["accountBalance"] == 750.0
    assert receiver_me["accountBalance"] == 250.0


async def test_transfer_is_rejected_when_funds_are_insufficient(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 100.0)

    response = await sender.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 500.0, "receiverUsername": "alice"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Insufficient funds"
    assert response.json()["data"]["code"] == "insufficient_funds"

    me = (await sender.get("/api/v1/users/me")).json()["data"]
    assert me["accountBalance"] == 100.0


async def test_transfer_to_an_unknown_user_is_a_404(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 500.0)

    response = await sender.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 10.0, "receiverUsername": "nobody"},
    )
    assert response.status_code == 404


async def test_transfer_to_self_is_rejected(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 500.0)

    response = await sender.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 10.0, "receiverUsername": "tester"},
    )
    assert response.status_code == 400
    assert "yourself" in response.json()["message"]


async def test_transfer_without_a_receiver_is_rejected(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 500.0)

    response = await sender.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 10.0},
    )
    assert response.status_code == 400
    assert "receiverUsername" in response.json()["message"]


async def test_shopping_needs_no_counterparty_and_is_an_outflow(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 500.0)

    response = await sender.post(
        "/api/v1/transactions",
        json={"type": "shopping", "amount": 40.0, "description": "Groceries"},
    )

    assert response.status_code == 201, response.text
    body = response.json()["data"]
    assert body["direction"] == "OUT"
    assert body["receiverUsername"] == "BankDash"
    assert body["description"] == "Groceries"


async def test_incomes_and_expenses_split_by_direction(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 1_000.0)
    await sender.post(
        "/api/v1/transactions", json={"type": "shopping", "amount": 100.0}
    )
    await sender.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 200.0, "receiverUsername": "alice"},
    )

    everything = (await sender.get("/api/v1/transactions")).json()["data"]
    incomes = (await sender.get("/api/v1/transactions/incomes")).json()["data"]
    expenses = (await sender.get("/api/v1/transactions/expenses")).json()["data"]

    assert everything["totalItems"] == 3
    assert incomes["totalItems"] == 1
    assert all(i["direction"] == "IN" for i in incomes["items"])
    assert expenses["totalItems"] == 2
    assert all(e["direction"] == "OUT" for e in expenses["items"])


async def test_pagination_is_zero_indexed_and_consistent(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 500.0)
    for index in range(7):
        await sender.post(
            "/api/v1/transactions", json={"type": "shopping", "amount": float(index + 1)}
        )

    async def page(n: int) -> dict:
        response = await sender.get(
            "/api/v1/transactions", params={"page": n, "size": 3}
        )
        return response.json()["data"]

    first, second, third = await page(0), await page(1), await page(2)

    assert first["totalItems"] == 8
    assert first["totalPages"] == 3
    assert first["hasNext"] is True
    assert first["hasPrevious"] is False
    assert second["hasNext"] is True and second["hasPrevious"] is True
    assert third["hasNext"] is False and len(third["items"]) == 2

    seen = [i["id"] for p in (first, second, third) for i in p["items"]]
    assert len(set(seen)) == 8


async def test_timestamps_serialise_as_utc_iso(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 100.0)

    items = (await sender.get("/api/v1/transactions")).json()["data"]["items"]
    assert items[0]["occurredAt"].endswith("Z")


async def test_balance_history_reconstructs_history(client_factory):
    sender, _ = await _two_accounts(client_factory)
    await _fund(sender, 1_000.0)
    await sender.post(
        "/api/v1/transactions", json={"type": "shopping", "amount": 400.0}
    )

    response = await sender.get(
        "/api/v1/transactions/balance-history", params={"months": 6}
    )
    points = response.json()["data"]

    assert len(points) == 6
    assert points[-1]["value"] == 600.0  # current balance is the final point
    # Both movements happened this month, so the account was still empty at the
    # start of it - every earlier point must therefore be 0.
    assert all(p["value"] == 0.0 for p in points[:-1])


async def test_transfer_recipients_lists_other_users(client_factory):
    sender, receiver = await _two_accounts(client_factory)
    await register(receiver, name="Bob", email="bob@bankdash.dev", username="bob")

    response = await sender.get("/api/v1/transactions/transfer-recipients")
    recipients = response.json()["data"]

    names = {r["username"] for r in recipients}
    assert "tester" not in names  # never suggest yourself
    assert {"alice", "bob"} <= names


async def test_get_transaction_by_id_and_isolation(client_factory):
    sender, receiver = await _two_accounts(client_factory)
    await _fund(sender, 1_000.0)
    created = await sender.post(
        "/api/v1/transactions",
        json={"type": "transfer", "amount": 25.0, "receiverUsername": "alice"},
    )
    txn_id = created.json()["data"]["id"]

    own = await sender.get(f"/api/v1/transactions/{txn_id}")
    assert own.status_code == 200

    # Alice holds her own leg under a different id, so the sender's row must not
    # be readable by anyone else.
    assert (
        await receiver.get(f"/api/v1/transactions/{txn_id}")
    ).status_code == 404

    assert (
        await sender.get("/api/v1/transactions/does-not-exist")
    ).status_code == 404


async def test_amount_must_be_positive(client_factory):
    sender, _ = await _two_accounts(client_factory)

    response = await sender.post(
        "/api/v1/transactions", json={"type": "shopping", "amount": -5}
    )
    assert response.status_code == 422
    assert response.json()["success"] is False
