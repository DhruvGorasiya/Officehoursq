"""
Integration tests for POST /api/v1/auth/register,
                     POST /api/v1/auth/login,
                     GET  /api/v1/auth/me

Uses the real Supabase project — no mocking.
Each test creates its own uniquely-named account via uuid4.

Notes on design decisions:
  * Email domain: @testsuite.dev — Pydantic EmailStr (email-validator) rejects
    RFC-2606 reserved TLDs (.invalid, .test, .local) as well as some others.
    A real-looking eTLD is required; we use @testsuite.dev which passes
    email-validator's DNS-free syntax check.
  * /me 401 shape: when no/bad Authorization header is sent, FastAPI's own
    HTTPBearer raises BEFORE the route handler runs, returning the standard
    FastAPI error body {"detail": "..."} — NOT our custom {"success": false, ...}.
    Tests for those cases therefore assert on the "detail" key.
"""

import uuid
from unittest.mock import patch
import pytest  # noqa: F401
from httpx import AsyncClient

from app.core.database import supabase

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE = "/api/v1/auth"
# Must be a syntactically valid email that passes email-validator's checks.
# The domain doesn't need to resolve — email-validator only does syntax checks
# in its default (non-deliverability) mode.
EMAIL_DOMAIN = "testsuite.dev"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique_email(role: str = "user") -> str:
    uid = uuid.uuid4().hex[:8]
    return f"test_{role}_{uid}@{EMAIL_DOMAIN}"


def _reg_payload(role: str = "student") -> dict:
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"test_{role}_{uid}@{EMAIL_DOMAIN}",
        "password": "TestPass123!",
        "name": f"Test {role.capitalize()} {uid}",
        "role": role,
    }


async def _register(client: AsyncClient, payload: dict):
    return await client.post(f"{BASE}/register", json=payload)


async def _login(client: AsyncClient, email: str, password: str):
    return await client.post(f"{BASE}/login", json={"email": email, "password": password})


# ===========================================================================
# POST /register
# ===========================================================================

class TestRegister:

    async def test_professor_registration_success(self, client: AsyncClient):
        """Valid professor payload → 200, success=True, token present."""
        payload = _reg_payload("professor")
        res = await _register(client, payload)

        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        if data.get("requires_confirmation"):
            pytest.skip("Supabase email confirmation is enabled — skipping token checks")
        assert data["token"], "JWT token must not be empty"
        assert data["email"] == payload["email"]
        assert data["role"] == "professor"
        assert "id" in data
        assert "name" in data

    async def test_ta_registration_success(self, client: AsyncClient):
        """Valid TA payload → 200, success=True."""
        payload = _reg_payload("ta")
        res = await _register(client, payload)

        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        if data.get("requires_confirmation"):
            pytest.skip("Supabase email confirmation is enabled")
        assert data["role"] == "ta"
        assert data["email"] == payload["email"]

    async def test_student_registration_success(self, client: AsyncClient):
        """Valid student payload → 200, success=True."""
        payload = _reg_payload("student")
        res = await _register(client, payload)

        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        if data.get("requires_confirmation"):
            pytest.skip("Supabase email confirmation is enabled")
        assert data["role"] == "student"

    async def test_register_missing_email(self, client: AsyncClient):
        """Omitting email → 422 (Pydantic validation)."""
        res = await _register(
            client,
            {"password": "TestPass123!", "name": "No Email", "role": "student"},
        )
        assert res.status_code == 422

    async def test_register_missing_password(self, client: AsyncClient):
        """Omitting password → 422."""
        res = await _register(
            client,
            {"email": _unique_email(), "name": "No Pass", "role": "student"},
        )
        assert res.status_code == 422

    async def test_register_missing_name(self, client: AsyncClient):
        """Omitting name → 422."""
        res = await _register(
            client,
            {"email": _unique_email(), "password": "TestPass123!", "role": "student"},
        )
        assert res.status_code == 422

    async def test_register_invalid_role(self, client: AsyncClient):
        """role='admin' is not in the UserRole enum → 422."""
        res = await _register(
            client,
            {
                "email": _unique_email("admin"),
                "password": "TestPass123!",
                "name": "Invalid Role",
                "role": "admin",
            },
        )
        assert res.status_code == 422

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Registering the same email twice → second attempt returns 400."""
        payload = _reg_payload("student")

        first = await _register(client, payload)
        assert first.status_code == 200
        if first.json()["data"].get("requires_confirmation"):
            pytest.skip("Supabase email confirmation is enabled")

        second = await _register(client, payload)
        assert second.status_code == 400
        assert second.json()["success"] is False

    @patch.object(supabase, "table")
    async def test_register_db_exception(self, mock_table, client: AsyncClient):
        """Auth succeeds but public.users insert fails -> 400."""
        # Mock insert().execute()
        mock_table.return_value.insert.return_value.execute.side_effect = Exception("DB Insert Error")
        
        payload = _reg_payload("student")
        res = await _register(client, payload)
        
        assert res.status_code == 400
        assert "profile creation failed" in res.json()["message"]


# ===========================================================================
# POST /login
# ===========================================================================

class TestLogin:

    async def test_login_valid_credentials(self, client: AsyncClient):
        """Register then login → 200, token present, correct email in data."""
        payload = _reg_payload("student")
        reg = await _register(client, payload)
        assert reg.status_code == 200
        if reg.json()["data"].get("requires_confirmation"):
            pytest.skip("Supabase email confirmation is enabled")

        res = await _login(client, payload["email"], payload["password"])
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["token"], "JWT token must not be empty"
        assert data["email"] == payload["email"]
        assert "id" in data
        assert "name" in data
        assert "role" in data

    async def test_login_wrong_password(self, client: AsyncClient):
        """Correct email, wrong password → 401, success=False."""
        payload = _reg_payload("student")
        reg = await _register(client, payload)
        assert reg.status_code == 200
        if reg.json()["data"].get("requires_confirmation"):
            pytest.skip("Supabase email confirmation is enabled")

        res = await _login(client, payload["email"], "WrongPassword999!")
        assert res.status_code == 401
        assert res.json()["success"] is False

    async def test_login_email_not_found(self, client: AsyncClient):
        """Non-existent email → 401, success=False."""
        res = await _login(client, f"nobody_{uuid.uuid4().hex[:6]}@{EMAIL_DOMAIN}", "TestPass123!")
        assert res.status_code == 401
        assert res.json()["success"] is False

    @patch.object(supabase, "table")
    async def test_login_fallback_metadata(self, mock_table, client: AsyncClient):
        """User exists in Auth but not in public.users → falls back to metadata."""
        # Mock select().eq().single().execute() to raise exception
        mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB Error")
        
        payload = _reg_payload("student")
        reg = await _register(client, payload)
        assert reg.status_code == 200
        
        res = await _login(client, payload["email"], payload["password"])
        assert res.status_code == 200
        assert res.json()["data"]["name"] == payload["name"]
        assert res.json()["data"]["role"] == "student"


# ===========================================================================
# GET /me
# ===========================================================================

class TestMe:

    async def test_me_valid_token(self, client: AsyncClient):
        """Valid Bearer JWT → 200, correct id / email / name / role fields."""
        payload = _reg_payload("professor")
        reg = await _register(client, payload)
        assert reg.status_code == 200
        reg_body = reg.json()
        if reg_body["data"].get("requires_confirmation"):
            pytest.skip("Supabase email confirmation is enabled")

        token = reg_body["data"]["token"]
        res = await client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["email"] == payload["email"]
        assert data["role"] == "professor"
        assert "id" in data
        assert "name" in data

    async def test_me_no_auth_header(self, client: AsyncClient):
        """No Authorization header → 401 (HTTPBearer requires the header).

        FastAPI's HTTPBearer raises an HTTPException when no credentials are
        provided and returns the standard FastAPI error body {"detail": "..."}
        — NOT our custom {"success": false} shape.
        """
        res = await client.get(f"{BASE}/me")
        # HTTPBearer with auto_error=True raises 401 when header is absent
        assert res.status_code == 401
        body = res.json()
        assert "detail" in body

    async def test_me_malformed_token(self, client: AsyncClient):
        """Bearer with a garbage token → 401, FastAPI error body with 'detail' key.

        The dependency calls supabase.auth.get_user() which rejects the bad token
        and re-raises as HTTP 401.  FastAPI returns {"detail": "..."}.
        """
        res = await client.get(
            f"{BASE}/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert res.status_code == 401
        body = res.json()
        assert "detail" in body

    @patch.object(supabase, "table")
    async def test_me_user_not_found(self, mock_table, client: AsyncClient):
        """Valid token but user missing from public.users -> 404."""
        import unittest.mock
        mock_response = unittest.mock.MagicMock()
        mock_response.data = None
        mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        payload = _reg_payload("ta")
        reg = await _register(client, payload)
        assert reg.status_code == 200
        token = reg.json()["data"]["token"]
        
        res = await client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 404
        assert res.json()["success"] is False
        assert "not found" in res.json()["message"].lower()

    @patch.object(supabase, "table")
    async def test_me_user_db_exception(self, mock_table, client: AsyncClient):
        """Valid token but DB throws exception -> 400."""
        mock_table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB Error")
        
        payload = _reg_payload("student")
        reg = await _register(client, payload)
        token = reg.json()["data"]["token"]
        
        res = await client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 400
