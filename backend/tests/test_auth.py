"""Auth: registration, login, token rotation, and password changes."""

from httpx import AsyncClient

from tests.conftest import auth_headers, login, register


async def test_register_returns_the_created_user(client: AsyncClient):
    body = await register(client)

    assert body["username"] == "tester"
    assert body["email"] == "test@bankdash.dev"
    assert body["role"] == "USER"
    assert body["accountBalance"] == 0.0
    assert "password" not in body
    assert "hashedPassword" not in body
    assert body["preferences"]["currency"] == "USD"


async def test_register_rejects_a_duplicate_username(client: AsyncClient):
    await register(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Someone Else",
            "email": "other@bankdash.dev",
            "username": "tester",
            "password": "12345678",
            "dateOfBirth": "1991-01-01",
            "permanentAddress": "a",
            "presentAddress": "b",
            "postalCode": "10001",
            "city": "NY",
            "country": "US",
        },
    )

    assert response.status_code == 409
    assert response.json()["success"] is False
    assert "username" in response.json()["message"]


async def test_login_returns_camel_case_token_pair(client: AsyncClient):
    await register(client)
    tokens = await login(client)

    assert tokens["tokenType"] == "Bearer"
    assert tokens["accessToken"]
    assert tokens["refreshToken"]
    assert tokens["expiresIn"] > 0


async def test_login_is_case_insensitive_on_username(client: AsyncClient):
    await register(client)
    tokens = await login(client, username="TeStEr")

    assert tokens["accessToken"]


async def test_login_rejects_a_bad_password(client: AsyncClient):
    await register(client)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "tester", "password": "wrong"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "message": "Invalid username or password",
        "data": {"code": "unauthorized"},
    }


async def test_protected_route_requires_a_token(client: AsyncClient):
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["data"]["code"] == "unauthorized"


async def test_protected_route_rejects_a_garbage_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert response.status_code == 401
    assert response.json()["data"]["code"] == "invalid_token"


async def test_refresh_rotates_and_invalidates_the_old_token(client: AsyncClient):
    await register(client)
    tokens = await login(client)

    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": tokens["refreshToken"]}
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()["data"]
    assert new_tokens["refreshToken"] != tokens["refreshToken"]

    # The new access token works.
    ok = await client.get("/api/v1/users/me", headers=auth_headers(new_tokens))
    assert ok.status_code == 200

    # Replaying the old refresh token is rejected.
    replay = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": tokens["refreshToken"]}
    )
    assert replay.status_code == 401
    assert "already been used" in replay.json()["message"]


async def test_change_password_requires_the_current_one(client: AsyncClient):
    await register(client)
    tokens = await login(client)

    rejected = await client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "nope", "newPassword": "newpassword123"},
        headers=auth_headers(tokens),
    )
    assert rejected.status_code == 401

    accepted = await client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "12345678", "newPassword": "newpassword123"},
        headers=auth_headers(tokens),
    )
    assert accepted.status_code == 200

    assert (await login(client, password="newpassword123"))["accessToken"]
    assert (await client.post(
        "/api/v1/auth/login", json={"username": "tester", "password": "12345678"}
    )).status_code == 401


async def test_change_password_revokes_outstanding_refresh_tokens(client: AsyncClient):
    await register(client)
    tokens = await login(client)

    await client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "12345678", "newPassword": "newpassword123"},
        headers=auth_headers(tokens),
    )

    response = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": tokens["refreshToken"]}
    )
    assert response.status_code == 401


async def test_logout_revokes_the_refresh_token(client: AsyncClient):
    await register(client)
    tokens = await login(client)

    assert (await client.post(
        "/api/v1/auth/logout",
        json={"refreshToken": tokens["refreshToken"]},
        headers=auth_headers(tokens),
    )).status_code == 200

    assert (await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": tokens["refreshToken"]}
    )).status_code == 401