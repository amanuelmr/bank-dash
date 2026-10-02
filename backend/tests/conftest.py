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
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


async def register(client: AsyncClient, **overrides) -> dict:
    payload = {**DEFAULT_REGISTRATION, **overrides}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def login(client: AsyncClient, username: str = "tester", password: str = "12345678") -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def auth_headers(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['accessToken']}"}


@pytest_asyncio.fixture
async def account(client: AsyncClient) -> dict:
    """A registered + authenticated user, with tokens and an auth header helper."""
    await register(client)
    tokens = await login(client)
    return {
        "tokens": tokens,
        "headers": auth_headers(tokens),
        "user": await client.get("/api/v1/users/me", headers=auth_headers(tokens)),
    }