"""
conftest.py – shared pytest fixtures for the OfficeHoursQ FastAPI test suite.

All fixtures are function-scoped and use the real Supabase test project
(no mocking). UUIDs in email addresses prevent inter-test collisions.
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """An httpx AsyncClient wired directly to the FastAPI ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _register_and_login(client: AsyncClient, role: str) -> str:
    """Register a fresh user with *role* and return their JWT access token."""
    uid = uuid.uuid4().hex[:8]
    email = f"test_{role}_{uid}@testsuite.dev"
    password = "TestPass123!"
    name = f"Test {role.capitalize()} {uid}"

    # Register
    reg_res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={"email": email, "password": password, "name": name, "role": role},
    )

    body = reg_res.json()

    # If email confirmation is required, fall back to service-role sign-in
    if body.get("data", {}).get("requires_confirmation"):
        # Try logging in directly – Supabase test projects often disable
        # email confirmation by default, so this path is a safety net.
        login_res = await client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            json={"email": email, "password": password},
        )
        login_body = login_res.json()
        assert login_res.status_code == 200, (
            f"Login after register failed for {role}: {login_body}"
        )
        return login_body["data"]["token"]

    assert reg_res.status_code == 200, (
        f"Registration failed for {role}: {body}"
    )
    return body["data"]["token"]


# ---------------------------------------------------------------------------
# Role-specific token fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def professor_token(client: AsyncClient) -> str:
    """JWT for a freshly-registered professor test user."""
    return await _register_and_login(client, "professor")


@pytest_asyncio.fixture
async def ta_token(client: AsyncClient) -> str:
    """JWT for a freshly-registered TA test user."""
    return await _register_and_login(client, "ta")


@pytest_asyncio.fixture
async def student_token(client: AsyncClient) -> str:
    """JWT for a freshly-registered student test user."""
    return await _register_and_login(client, "student")
