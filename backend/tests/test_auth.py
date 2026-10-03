"""Auth: registration, cookie issuance, rotation, and password changes."""

from httpx import AsyncClient

from tests.conftest import access_token_from_cookies, auth_headers, login, register


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


async def test_login_sets_httponly_cookies(client: AsyncClient):
    await register(client)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "tester", "password": "12345678"}
    )

    assert response.status_code == 200
    cookies = response.headers.get_list("set-cookie")
    joined = "; ".join(cookies)
    assert "accessToken=" in joined
    assert "refreshToken=" in joined
    # The whole point of this change: page scripts must not be able to read them.
    assert "HttpOnly" in joined
    assert joined.lower().count("httponly") == 2


async def test_login_does_not_return_tokens_in_the_body(client: AsyncClient):
    await register(client)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "tester", "password": "12345678"}
    )

    text = response.text
    assert "accessToken" not in text
    assert "refreshToken" not in text
    assert response.json()["data"]["username"] == "tester"


async def test_login_is_case_insensitive_on_username(client: AsyncClient):
    await register(client)
    body = await login(client, username="TeStEr")
    assert body["username"] == "tester"


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


async def test_protected_route_rejects_a_garbage_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert response.status_code == 401
    assert response.json()["data"]["code"] == "invalid_token"


async def test_cookie_alone_authenticates_a_request(client: AsyncClient):
    """The browser sends no Authorization header - the cookie must be enough."""
    await register(client)
    await login(client)

    client.cookies.clear()  # start from a clean jar, then restore from login
    await login(client)

    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "tester"


async def test_bearer_header_still_works_for_non_browser_clients(client: AsyncClient):
    """Regression guard: CLI clients and the smoke script send a header."""
    await register(client)
    await login(client)
    token = access_token_from_cookies(client)

    client.cookies.clear()  # drop the cookies: the header must stand alone
    response = await client.get("/api/v1/users/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "tester"


async def test_refresh_rotates_the_cookie_with_no_body(client: AsyncClient):
    await register(client)
    await login(client)
    before = client.cookies.get("refreshToken")

    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert client.cookies.get("refreshToken") != before


async def test_replaying_an_old_refresh_token_is_rejected(client: AsyncClient):
    await register(client)
    await login(client)
    stale = client.cookies.get("refreshToken")

    assert (await client.post("/api/v1/auth/refresh")).status_code == 200

    # Restore the consumed token and try to use it again.
    client.cookies.set("refreshToken", stale)
    replay = await client.post("/api/v1/auth/refresh")
    assert replay.status_code == 401
    assert "already been used" in replay.json()["message"]


async def test_refresh_without_a_token_is_rejected(client: AsyncClient):
    client.cookies.clear()
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


async def test_change_password_requires_the_current_one(client: AsyncClient):
    await register(client)
    await login(client)

    rejected = await client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "nope", "newPassword": "newpassword123"},
    )
    assert rejected.status_code == 401

    accepted = await client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "12345678", "newPassword": "newpassword123"},
    )
    assert accepted.status_code == 200

    client.cookies.clear()
    assert (await login(client, password="newpassword123"))["username"] == "tester"
    assert (
        await client.post(
            "/api/v1/auth/login", json={"username": "tester", "password": "12345678"}
        )
    ).status_code == 401


async def test_change_password_revokes_outstanding_refresh_tokens(client: AsyncClient):
    await register(client)
    await login(client)
    stale = client.cookies.get("refreshToken")

    await client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "12345678", "newPassword": "newpassword123"},
    )

    client.cookies.set("refreshToken", stale)
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401


async def test_logout_revokes_the_token_and_clears_cookies(client: AsyncClient):
    await register(client)
    await login(client)
    stale = client.cookies.get("refreshToken")

    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200

    cleared = "; ".join(response.headers.get_list("set-cookie"))
    assert "accessToken=" in cleared and "Max-Age=0" in cleared

    client.cookies.set("refreshToken", stale)
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401