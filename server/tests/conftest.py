"""
conftest.py – shared pytest fixtures for the OfficeHoursQ FastAPI test suite.

Design decisions:
  * `client` is function-scoped — a fresh AsyncClient per test (cheap, stateless).
  * Token fixtures are SESSION-scoped — each role is registered ONCE per pytest
    invocation. This minimises Supabase auth API calls across the full test suite.
  * `_register_and_login` retries with exponential backoff on 429 rate-limit
    responses so that the full suite (auth + courses + sessions) can run without
    manual wait times between individual files.
  * A dedicated `_session_client` (session-scoped) drives the token fixtures since
    session-scoped fixtures cannot depend on function-scoped ones.
  * UUIDs in email addresses prevent collisions across different sessions/runs.
"""

import asyncio
import uuid
import pytest  # noqa: F401
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings

_AUTH_BASE = f"{settings.API_V1_PREFIX}/auth"


# ---------------------------------------------------------------------------
# HTTP client — function-scoped (fresh per test for isolation)
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
# Internal session-scoped client used by the token fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def _session_client() -> AsyncClient:
    """Long-lived client shared among session-scoped token fixtures."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helper with retry-backoff for Supabase 429 rate limiting
# ---------------------------------------------------------------------------

async def _register_and_login(
    client: AsyncClient,
    role: str,
    *,
    max_retries: int = 5,
    base_wait: float = 10.0,
) -> str:
    """Register a fresh user with *role*, return their JWT access token.

    Retries up to *max_retries* times with exponential backoff if Supabase
    returns a 429 / 'Request rate limit reached' response.
    """
    uid = uuid.uuid4().hex[:8]
    email = f"test_{role}_{uid}@testsuite.dev"
    password = "TestPass123!"
    name = f"Test {role.capitalize()} {uid}"

    for attempt in range(max_retries):
        reg_res = await client.post(
            f"{_AUTH_BASE}/register",
            json={"email": email, "password": password, "name": name, "role": role},
        )
        body = reg_res.json()

        # Handle Supabase 429 rate limiting — wait and retry
        rate_limited = (
            reg_res.status_code == 400
            and "rate limit" in body.get("message", "").lower()
        )
        if rate_limited:
            wait = base_wait * (2 ** attempt)
            await asyncio.sleep(wait)
            continue

        # Handle email-confirmation-required flow
        if body.get("data", {}).get("requires_confirmation"):
            login_res = await client.post(
                f"{_AUTH_BASE}/login",
                json={"email": email, "password": password},
            )
            login_body = login_res.json()
            assert login_res.status_code == 200, (
                f"Login after register failed for {role}: {login_body}"
            )
            return login_body["data"]["token"]

        assert reg_res.status_code == 200, (
            f"Registration failed for {role} (attempt {attempt + 1}): {body}"
        )
        return body["data"]["token"]

    raise RuntimeError(
        f"Supabase auth rate limit not cleared after {max_retries} retries "
        f"for role '{role}'. Try increasing base_wait or running suites separately."
    )


# ---------------------------------------------------------------------------
# Role-specific token fixtures — SESSION-scoped
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def professor_token(_session_client: AsyncClient) -> str:
    """JWT for a professor test user (registered once per pytest session)."""
    return await _register_and_login(_session_client, "professor")


@pytest_asyncio.fixture(scope="session")
async def ta_token(_session_client: AsyncClient) -> str:
    """JWT for a TA test user (registered once per pytest session)."""
    return await _register_and_login(_session_client, "ta")


@pytest_asyncio.fixture(scope="session")
async def student_token(_session_client: AsyncClient) -> str:
    """JWT for a student test user (registered once per pytest session)."""
    return await _register_and_login(_session_client, "student")
