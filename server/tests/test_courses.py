"""
Integration tests for POST   /api/v1/courses
                     GET    /api/v1/courses
                     GET    /api/v1/courses/{course_id}
                     POST   /api/v1/courses/join

Uses the real Supabase project — no mocking.
Each test is self-contained: courses are created inline as needed.

FastAPI behaviour notes (confirmed from route source):
  * require_role() uses HTTPBearer + role check → 401 when no token, 403 when
    wrong role (both via HTTPException/JSONResponse).
  * POST /join with bad invite_code → 404 (not 400) per route implementation.
  * POST /join by a professor → 403.
  * POST /join when already enrolled → 400.
"""

import uuid
import pytest  # noqa: F401
from httpx import AsyncClient

BASE = "/api/v1/courses"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _course_name() -> str:
    uid = uuid.uuid4().hex[:6].upper()
    return f"CS-{uid} Test Course"


async def _create_course(client: AsyncClient, token: str, name: str | None = None) -> dict:
    """Professor creates a course; returns the course data dict."""
    payload = {"name": name or _course_name()}
    res = await client.post(
        BASE,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, f"Course creation failed: {res.json()}"
    return res.json()["data"]


async def _join_course(client: AsyncClient, token: str, invite_code: str):
    """Helper to join a course by invite code."""
    return await client.post(
        f"{BASE}/join",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {token}"},
    )


# ===========================================================================
# POST /api/v1/courses  — Create course
# ===========================================================================

class TestCreateCourse:

    async def test_professor_creates_course_success(
        self, client: AsyncClient, professor_token: str
    ):
        """Professor creates a course → 200, course data with 6-char invite_code."""
        name = _course_name()
        res = await client.post(
            BASE,
            json={"name": name},
            headers={"Authorization": f"Bearer {professor_token}"},
        )

        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["name"] == name
        assert "id" in data
        assert "professor_id" in data
        invite = data.get("invite_code", "")
        assert len(invite) == 6, f"invite_code must be 6 chars, got: {invite!r}"

    async def test_ta_cannot_create_course(
        self, client: AsyncClient, ta_token: str
    ):
        """TA tries to create a course → 403."""
        res = await client.post(
            BASE,
            json={"name": _course_name()},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_student_cannot_create_course(
        self, client: AsyncClient, student_token: str
    ):
        """Student tries to create a course → 403."""
        res = await client.post(
            BASE,
            json={"name": _course_name()},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_cannot_create_course(self, client: AsyncClient):
        """No token → 401."""
        res = await client.post(BASE, json={"name": _course_name()})
        assert res.status_code == 401

    async def test_create_course_missing_name(
        self, client: AsyncClient, professor_token: str
    ):
        """Missing name field → 422 (Pydantic validation)."""
        res = await client.post(
            BASE,
            json={},
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 422


# ===========================================================================
# GET /api/v1/courses  — List courses
# ===========================================================================

class TestListCourses:

    async def test_professor_sees_own_course(
        self, client: AsyncClient, professor_token: str
    ):
        """After creating a course, professor's list includes it."""
        course = await _create_course(client, professor_token)
        course_id = course["id"]

        res = await client.get(
            BASE,
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        ids = [c["id"] for c in body["data"]]
        assert course_id in ids, "Newly created course not found in professor's list"

    async def test_student_sees_enrolled_course(
        self, client: AsyncClient, professor_token: str, student_token: str
    ):
        """After joining, student's list includes the course."""
        course = await _create_course(client, professor_token)
        invite_code = course["invite_code"]
        course_id = course["id"]

        join_res = await _join_course(client, student_token, invite_code)
        assert join_res.status_code == 200

        res = await client.get(
            BASE,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        ids = [c["id"] for c in body["data"]]
        assert course_id in ids, "Joined course not found in student's list"

    async def test_unauthenticated_list_rejected(self, client: AsyncClient):
        """No token → 401."""
        res = await client.get(BASE)
        assert res.status_code == 401


# ===========================================================================
# GET /api/v1/courses/{course_id}  — Get course by ID
# ===========================================================================

class TestGetCourse:

    async def test_enrolled_user_can_fetch_course(
        self, client: AsyncClient, professor_token: str, student_token: str
    ):
        """Student who joined can fetch the course by ID."""
        course = await _create_course(client, professor_token)
        await _join_course(client, student_token, course["invite_code"])

        res = await client.get(
            f"{BASE}/{course['id']}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["id"] == course["id"]
        assert data["name"] == course["name"]
        assert "invite_code" in data
        assert "professor_id" in data

    async def test_nonexistent_course_returns_404(
        self, client: AsyncClient, professor_token: str
    ):
        """Random UUID that doesn't exist → 404."""
        fake_id = str(uuid.uuid4())
        res = await client.get(
            f"{BASE}/{fake_id}",
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 404
        body = res.json()
        assert body["success"] is False

    async def test_unauthenticated_get_course_rejected(
        self, client: AsyncClient, professor_token: str
    ):
        """No token → 401."""
        course = await _create_course(client, professor_token)
        res = await client.get(f"{BASE}/{course['id']}")
        assert res.status_code == 401


# ===========================================================================
# POST /api/v1/courses/join  — Join course
# ===========================================================================

class TestJoinCourse:

    async def test_student_joins_with_valid_invite_code(
        self, client: AsyncClient, professor_token: str, student_token: str
    ):
        """Student joins with a valid invite_code → 200, enrollment data returned,
        course appears in student's course list."""
        course = await _create_course(client, professor_token)
        invite_code = course["invite_code"]

        res = await _join_course(client, student_token, invite_code)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["course_id"] == course["id"]
        assert "user_id" in data
        assert "role" in data

        # Verify course appears in student's list
        list_res = await client.get(
            BASE, headers={"Authorization": f"Bearer {student_token}"}
        )
        ids = [c["id"] for c in list_res.json()["data"]]
        assert course["id"] in ids

    async def test_ta_joins_with_valid_invite_code(
        self, client: AsyncClient, professor_token: str, ta_token: str
    ):
        """TA joins with a valid invite_code → 200."""
        course = await _create_course(client, professor_token)

        res = await _join_course(client, ta_token, course["invite_code"])
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["course_id"] == course["id"]

    async def test_join_invalid_invite_code(
        self, client: AsyncClient, student_token: str
    ):
        """Non-existent 6-char invite code → 404 (route uses single() which
        raises when 0 rows found, mapped to 404 by the handler)."""
        res = await _join_course(client, student_token, "ZZZZZZ")
        assert res.status_code == 404
        assert res.json()["success"] is False

    async def test_join_already_enrolled(
        self, client: AsyncClient, professor_token: str, student_token: str
    ):
        """Joining the same course twice → 400, success=False."""
        course = await _create_course(client, professor_token)
        invite_code = course["invite_code"]

        first = await _join_course(client, student_token, invite_code)
        assert first.status_code == 200

        second = await _join_course(client, student_token, invite_code)
        assert second.status_code == 400
        assert second.json()["success"] is False

    async def test_join_unauthenticated_rejected(
        self, client: AsyncClient, professor_token: str
    ):
        """No token → 401."""
        course = await _create_course(client, professor_token)
        res = await client.post(
            f"{BASE}/join",
            json={"invite_code": course["invite_code"]},
        )
        assert res.status_code == 401
