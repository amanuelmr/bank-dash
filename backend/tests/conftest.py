"""Shared test fixtures: an isolated in-memory database and an HTTP client."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# A single shared in-memory connection: StaticPool keeps every session on the
# same connection so the schema created once is visible to all of them.
TEST_DATABASE_URL = "sqlite+aiosqlite://"

DEFAULT_REGISTRATION = {
    "name": "Test User",
    "email": "test@bankdash.dev",
    "username": "tester",
    "password": "12345678",
    "dateOfBirth": "1990-04-12",
    "permanentAddress": "100 Elm Street",
    "presentAddress": "200 Maple Avenue",
    "postalCode": "10001",
    "city": "New York",
    "country": "United States",
    "preferences": {"currency": "USD", "timeZone": "GMT-5"},
}


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )


@pytest_asyncio.fixture
async def client_factory(session_factory):
    """Build extra HTTP clients against the same isolated database.

    Auth is cookie based and a cookie jar belongs to one client, so acting as
    two different users means using two clients.
    """

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    created: list[AsyncClient] = []

    async def make() -> AsyncClient:
        http_client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        )
        created.append(http_client)
        return http_client

    try:
        yield make
    finally:
        for http_client in created:
            await http_client.aclose()
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(client_factory) -> AsyncIterator[AsyncClient]:
    async with await client_factory() as http_client:
        yield http_client


async def register(client: AsyncClient, **overrides) -> dict:
    payload = {**DEFAULT_REGISTRATION, **overrides}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def login(client: AsyncClient, username: str = "tester", password: str = "12345678") -> dict:
    """Sign in. httpx keeps the Set-Cookie values, so later calls are authenticated
    by cookie without any header."""
    response = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def access_token_from_cookies(client: AsyncClient) -> str:
    """Read the access token out of the client cookie jar.

    Only for tests that need to exercise the `Authorization: Bearer` path, which
    exists so CLI clients keep working now that the browser uses cookies.
    """
    return client.cookies.get("accessToken", "")


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
