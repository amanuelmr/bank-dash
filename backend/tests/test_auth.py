"""Auth: registration, cookie issuance, rotation, and password changes."""

from httpx import AsyncClient

from app.core.config import settings
from tests.conftest import access_token_from_cookies, auth_headers, login, register


def _set_cookies(response) -> dict[str, str]:
    """Set-Cookie headers keyed by cookie name."""
    return {
        cookie.split("=", 1)[0].strip(): cookie
        for cookie in response.headers.get_list("set-cookie")
    }


def _cookie_max_age(response, name: str) -> int:
    return int(_set_cookies(response)[name].split("Max-Age=", 1)[1].split(";", 1)[0])


def _api_domain(client: AsyncClient) -> str:
    """The cookie domain httpx recorded for this client's host.

    Read off the jar rather than derived from base_url: httpx normalises a bare
    hostname, so "http://test" is stored as "test.local".
    """
    return next((c.domain for c in client.cookies.jar if c.domain), "")


def _present_as(client: AsyncClient, token: str, domain: str) -> None:
    """Make `token` the client's refresh cookie, replacing whatever was there.

    Domain and path both have to match the cookie the API sets, because a cookie
    is keyed on (domain, path, name). Get either wrong and the two coexist, and
    httpx raises CookieConflict instead of guessing which to send.

    The domain is passed in because the client presenting a stolen token is often
    brand new - it has no cookies to copy it from - and its own jar is empty.
    """
    client.cookies.clear()
    client.cookies.set("refreshToken", token, domain=domain, path="/api/v1/auth")


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
    _present_as(client, stale, _api_domain(client))
    replay = await client.post("/api/v1/auth/refresh")
    assert replay.status_code == 401
    assert "already been used" in replay.json()["message"]


async def test_refresh_without_a_token_is_rejected(client: AsyncClient):
    client.cookies.clear()
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


async def test_failed_refresh_expires_both_cookies(client: AsyncClient):
    """A rejected refresh must clear the cookies, not just report the failure.

    JavaScript cannot delete an httpOnly cookie, so only the server can. Without
    this the dead cookie stays attached for its full 30-day lifetime and every
    API call first pays a refresh round-trip that is guaranteed to fail.
    """
    client.cookies.clear()
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    expiries = response.headers.get_list("set-cookie")
    # Both cookies, not one. Routing both through a single header mapping
    # collapses them under one `set-cookie` key and silently drops the second.
    assert len(expiries) == 2
    joined = "; ".join(expiries)
    assert "accessToken=" in joined
    assert "refreshToken=" in joined
    assert joined.count("Max-Age=0") == 2


async def test_replaying_a_consumed_refresh_cookie_expires_the_session(
    client: AsyncClient,
):
    """The stale-cookie path is the realistic one: a stolen-then-used token, not
    a missing cookie."""
    await register(client)
    await login(client)
    stale = client.cookies.get("refreshToken")
    assert (await client.post("/api/v1/auth/refresh")).status_code == 200

    _present_as(client, stale, _api_domain(client))
    replay = await client.post("/api/v1/auth/refresh")

    assert replay.status_code == 401
    assert "Max-Age=0" in "; ".join(replay.headers.get_list("set-cookie"))


async def test_cookies_are_scoped_so_the_refresh_token_stays_off_other_calls(
    client: AsyncClient,
):
    """The refresh token is only ever presented to /auth/refresh and
    /auth/logout. Scoped to "/" it would ride along with every API call, putting
    a 30-day credential into the reach of anything that logs request headers."""
    await register(client)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "tester", "password": "12345678"}
    )

    by_name = _set_cookies(response)
    assert "Path=/" in by_name["accessToken"]
    assert "Path=/api/v1/auth" in by_name["refreshToken"]


async def test_access_cookie_outlives_its_token(client: AsyncClient):
    """Wires the config invariant to what the server actually sends.

    A regression here is invisible in normal use: the session works right up
    until the exact hour the cookie dies, then everyone is silently signed out
    while still holding a valid refresh token.
    """
    await register(client)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "tester", "password": "12345678"}
    )

    max_age = _cookie_max_age(response, "accessToken")
    assert max_age > settings.access_token_expire_minutes * 60


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


async def test_logging_out_one_device_leaves_the_others_signed_in(client_factory):
    """Signing out is per-device. This used to revoke every outstanding token for
    the user, so a single logout could silently end sessions elsewhere."""
    phone = await client_factory()
    laptop = await client_factory()
    # One user, two sessions - the second client signs in rather than registering
    # again, since a second registration would be a duplicate username.
    await register(phone)
    await login(phone)
    await login(laptop)

    assert (await phone.post("/api/v1/auth/logout")).status_code == 200

    # The laptop's refresh token is untouched, so it still renews.
    assert (await laptop.post("/api/v1/auth/refresh")).status_code == 200
    assert (await laptop.get("/api/v1/users/me")).status_code == 200


async def test_logout_without_a_refresh_cookie_does_not_revoke_other_sessions(
    client_factory,
):
    """The realistic trigger: a device whose refresh cookie is already gone.

    Revoking "everything" because nothing was presented meant one stale device
    could sign a user out of all of them.
    """
    other = await client_factory()
    await register(other)
    await login(other)
    others_refresh = other.cookies.get("refreshToken")

    # A second session for the same user, holding an access token but no
    # refresh cookie at all - which is what a cleared or expired cookie looks
    # like from the API's side.
    orphan = await client_factory()
    orphan.cookies.set("accessToken", access_token_from_cookies(other))

    assert (await orphan.post("/api/v1/auth/logout")).status_code == 200

    other.cookies.set("refreshToken", others_refresh)
    assert (await other.post("/api/v1/auth/refresh")).status_code == 200


async def test_replaying_a_stolen_token_kills_everything_it_rotated_to(
    client_factory,
):
    """The attack this defends against.

    A thief steals one refresh token and quietly rotates it, so they hold a
    freshly-minted token. When the legitimate client later presents the stolen
    original, rejecting that token alone would leave the thief's replacement
    working for the full 30 days - which makes stealing one token a permanent
    takeover no matter how loudly the victim complains.
    """
    victim = await client_factory()
    await register(victim)
    await login(victim)

    stolen = victim.cookies.get("refreshToken")

    # The thief rotates the stolen token and keeps the replacement.
    thief = await client_factory()
    domain = _api_domain(victim)
    _present_as(thief, stolen, domain)
    assert (await thief.post("/api/v1/auth/refresh")).status_code == 200
    thief_token = thief.cookies.get("refreshToken")

    # The victim's copy is now the spent token, so presenting it is the replay
    # that reveals the theft.
    replay = await victim.post("/api/v1/auth/refresh")
    assert replay.status_code == 401
    assert "already been used" in replay.json()["message"]

    # ...and the thief's replacement dies with the family.
    _present_as(thief, thief_token, _api_domain(victim))
    assert (await thief.post("/api/v1/auth/refresh")).status_code == 401


async def test_replay_does_not_touch_other_devices(client_factory):
    """Killing the family must not become killing every session - that was the
    bug fixed in the previous branch, in a different direction."""
    victim = await client_factory()
    laptop = await client_factory()
    await register(victim)
    await login(victim)
    await login(laptop)

    stolen = victim.cookies.get("refreshToken")
    domain = _api_domain(victim)
    _present_as(victim, stolen, domain)
    assert (await victim.post("/api/v1/auth/refresh")).status_code == 200
    _present_as(victim, stolen, domain)

    assert (await victim.post("/api/v1/auth/refresh")).status_code == 401

    # The laptop signed in separately, so it has its own family and survives.
    assert (await laptop.post("/api/v1/auth/refresh")).status_code == 200
    assert (await laptop.get("/api/v1/users/me")).status_code == 200


async def test_logout_kills_tokens_the_session_had_rotated_to(client: AsyncClient):
    """Signing out must not leave a rotated copy of the same session usable."""
    await register(client)
    await login(client)

    rotated = client.cookies.get("refreshToken")
    assert (await client.post("/api/v1/auth/refresh")).status_code == 200

    domain = _api_domain(client)  # logout empties the jar; read this first
    assert (await client.post("/api/v1/auth/logout")).status_code == 200

    _present_as(client, rotated, domain)
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401


async def test_separate_sign_ins_get_separate_families(
    client_factory, session_factory
):
    """A family is one device's chain, so two devices must not share one."""
    first = await client_factory()
    second = await client_factory()
    await register(first)
    await login(first)
    await login(second)

    from sqlalchemy import select

    from app.models.user import RefreshToken

    async with session_factory() as db:
        families = list(await db.scalars(select(RefreshToken.family_id)))

    assert len(families) == 2
    assert len(set(families)) == 2
