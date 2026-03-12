"""
Integration tests for POST   /api/v1/sessions
                     GET    /api/v1/sessions?course_id=
                     GET    /api/v1/sessions/{session_id}
                     PUT    /api/v1/sessions/{session_id}
                     DELETE /api/v1/sessions/{session_id}
                     PATCH  /api/v1/sessions/{session_id}/status

Uses the real Supabase project — no mocking.
Each test creates its own course (and session where needed) so tests are
fully self-contained and order-independent.

Route implementation notes (from sessions.py):
  * POST / PUT / DELETE → require_role("professor") → 401 no-token, 403 wrong role
  * PATCH /status      → require_role("professor", "ta") → TAs CAN change status
  * Invalid status transition → 400 (e.g. scheduled→ended in one jump)
  * 404 is mapped from Supabase single()-row-not-found exception
"""

import uuid
import pytest
from httpx import AsyncClient

BASE = "/api/v1/sessions"
COURSES_BASE = "/api/v1/courses"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _session_payload(course_id: str) -> dict:
    uid = uuid.uuid4().hex[:4].upper()
    return {
        "course_id": course_id,
        "title": f"Test Session {uid}",
        "date": "2027-06-15",
        "start_time": "14:00:00",
        "end_time": "16:00:00",
    }


async def _make_course(client: AsyncClient, professor_token: str) -> dict:
    """Create a fresh course; return course data dict."""
    uid = uuid.uuid4().hex[:6].upper()
    res = await client.post(
        COURSES_BASE,
        json={"name": f"CS-{uid} Sessions Test"},
        headers={"Authorization": f"Bearer {professor_token}"},
    )
    assert res.status_code == 200, f"Course creation failed: {res.json()}"
    return res.json()["data"]


async def _make_session(
    client: AsyncClient, professor_token: str, course_id: str
) -> dict:
    """Create a scheduled session; return session data dict."""
    res = await client.post(
        BASE,
        json=_session_payload(course_id),
        headers={"Authorization": f"Bearer {professor_token}"},
    )
    assert res.status_code == 200, f"Session creation failed: {res.json()}"
    return res.json()["data"]


async def _patch_status(
    client: AsyncClient, token: str, session_id: str, new_status: str
):
    return await client.patch(
        f"{BASE}/{session_id}/status",
        json={"status": new_status},
        headers={"Authorization": f"Bearer {token}"},
    )


# ===========================================================================
# POST /api/v1/sessions  — Create session
# ===========================================================================

class TestCreateSession:

    async def test_professor_creates_session_success(
        self, client: AsyncClient, professor_token: str
    ):
        """Professor creates a session → 200, scheduled status, all fields present."""
        course = await _make_course(client, professor_token)
        payload = _session_payload(course["id"])

        res = await client.post(
            BASE,
            json=payload,
            headers={"Authorization": f"Bearer {professor_token}"},
        )

        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["title"] == payload["title"]
        assert data["course_id"] == course["id"]
        assert data["status"] == "scheduled"
        assert "id" in data
        assert "date" in data
        assert "start_time" in data
        assert "end_time" in data

    async def test_ta_cannot_create_session(
        self, client: AsyncClient, professor_token: str, ta_token: str
    ):
        """TA tries to create a session → 403."""
        course = await _make_course(client, professor_token)
        res = await client.post(
            BASE,
            json=_session_payload(course["id"]),
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_student_cannot_create_session(
        self, client: AsyncClient, professor_token: str, student_token: str
    ):
        """Student tries to create a session → 403."""
        course = await _make_course(client, professor_token)
        res = await client.post(
            BASE,
            json=_session_payload(course["id"]),
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_cannot_create_session(
        self, client: AsyncClient, professor_token: str
    ):
        """No token → 401."""
        course = await _make_course(client, professor_token)
        res = await client.post(BASE, json=_session_payload(course["id"]))
        assert res.status_code == 401

    async def test_create_session_missing_title(
        self, client: AsyncClient, professor_token: str
    ):
        """Missing required 'title' field → 422 (Pydantic validation)."""
        course = await _make_course(client, professor_token)
        payload = _session_payload(course["id"])
        payload.pop("title")

        res = await client.post(
            BASE,
            json=payload,
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 422


# ===========================================================================
# GET /api/v1/sessions?course_id=  — List sessions
# ===========================================================================

class TestListSessions:

    async def test_enrolled_user_sees_sessions(
        self, client: AsyncClient, professor_token: str, student_token: str
    ):
        """Enrolled student can list sessions for a course."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        # Student joins the course
        await client.post(
            f"{COURSES_BASE}/join",
            json={"invite_code": course["invite_code"]},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        res = await client.get(
            BASE,
            params={"course_id": course["id"]},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        ids = [s["id"] for s in body["data"]]
        assert session["id"] in ids

    async def test_unauthenticated_list_rejected(
        self, client: AsyncClient, professor_token: str
    ):
        """No token → 401."""
        course = await _make_course(client, professor_token)
        res = await client.get(BASE, params={"course_id": course["id"]})
        assert res.status_code == 401


# ===========================================================================
# GET /api/v1/sessions/{session_id}  — Get session by ID
# ===========================================================================

class TestGetSession:

    async def test_enrolled_user_can_fetch_session(
        self, client: AsyncClient, professor_token: str, student_token: str
    ):
        """Enrolled student fetches session by ID → 200 with expected fields."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        await client.post(
            f"{COURSES_BASE}/join",
            json={"invite_code": course["invite_code"]},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        res = await client.get(
            f"{BASE}/{session['id']}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["id"] == session["id"]
        assert data["title"] == session["title"]
        assert data["course_id"] == course["id"]
        assert "course_name" in data
        assert "tas" in data

    async def test_nonexistent_session_returns_404(
        self, client: AsyncClient, professor_token: str
    ):
        """Random UUID that doesn't exist → 404, success=False."""
        fake_id = str(uuid.uuid4())
        res = await client.get(
            f"{BASE}/{fake_id}",
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 404
        assert res.json()["success"] is False

    async def test_unauthenticated_get_session_rejected(
        self, client: AsyncClient, professor_token: str
    ):
        """No token → 401."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])
        res = await client.get(f"{BASE}/{session['id']}")
        assert res.status_code == 401


# ===========================================================================
# PUT /api/v1/sessions/{session_id}  — Update session
# ===========================================================================

class TestUpdateSession:

    async def test_professor_updates_scheduled_session(
        self, client: AsyncClient, professor_token: str
    ):
        """Professor updates title of a scheduled session → 200, new title returned."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])
        new_title = f"Updated Title {uuid.uuid4().hex[:4].upper()}"

        res = await client.put(
            f"{BASE}/{session['id']}",
            json={"title": new_title},
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["title"] == new_title

    async def test_cannot_update_active_session(
        self, client: AsyncClient, professor_token: str
    ):
        """Activated session cannot be updated → 400, success=False."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        # Activate the session
        patch = await _patch_status(client, professor_token, session["id"], "active")
        assert patch.status_code == 200

        res = await client.put(
            f"{BASE}/{session['id']}",
            json={"title": "Should Fail"},
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 400
        assert res.json()["success"] is False

    async def test_ta_cannot_update_session(
        self, client: AsyncClient, professor_token: str, ta_token: str
    ):
        """TA cannot update a session → 403."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        res = await client.put(
            f"{BASE}/{session['id']}",
            json={"title": "TA Update Attempt"},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_update_rejected(
        self, client: AsyncClient, professor_token: str
    ):
        """No token → 401."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])
        res = await client.put(f"{BASE}/{session['id']}", json={"title": "Anon"})
        assert res.status_code == 401


# ===========================================================================
# DELETE /api/v1/sessions/{session_id}  — Delete session
# ===========================================================================

class TestDeleteSession:

    async def test_professor_deletes_scheduled_session(
        self, client: AsyncClient, professor_token: str
    ):
        """Professor deletes a scheduled session → 200, success=True."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        res = await client.delete(
            f"{BASE}/{session['id']}",
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Confirm it's gone
        get_res = await client.get(
            f"{BASE}/{session['id']}",
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert get_res.status_code == 404

    async def test_cannot_delete_active_session(
        self, client: AsyncClient, professor_token: str
    ):
        """Active session cannot be deleted → 400."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        patch = await _patch_status(client, professor_token, session["id"], "active")
        assert patch.status_code == 200

        res = await client.delete(
            f"{BASE}/{session['id']}",
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 400
        assert res.json()["success"] is False

    async def test_ta_cannot_delete_session(
        self, client: AsyncClient, professor_token: str, ta_token: str
    ):
        """TA cannot delete a session → 403."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        res = await client.delete(
            f"{BASE}/{session['id']}",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_delete_rejected(
        self, client: AsyncClient, professor_token: str
    ):
        """No token → 401."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])
        res = await client.delete(f"{BASE}/{session['id']}")
        assert res.status_code == 401


# ===========================================================================
# PATCH /api/v1/sessions/{session_id}/status  — Change status
# ===========================================================================

class TestSessionStatus:

    async def test_professor_activates_session(
        self, client: AsyncClient, professor_token: str
    ):
        """Professor transitions scheduled → active → 200, status='active'."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        res = await _patch_status(client, professor_token, session["id"], "active")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["status"] == "active"

    async def test_professor_ends_session(
        self, client: AsyncClient, professor_token: str
    ):
        """Professor transitions active → ended → 200, status='ended'."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        activate = await _patch_status(client, professor_token, session["id"], "active")
        assert activate.status_code == 200

        res = await _patch_status(client, professor_token, session["id"], "ended")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["status"] == "ended"

    async def test_cannot_activate_while_another_session_active(
        self, client: AsyncClient, professor_token: str
    ):
        """Two sessions for the same course — activating the second while the first
        is already active → 400."""
        course = await _make_course(client, professor_token)
        session_a = await _make_session(client, professor_token, course["id"])
        session_b = await _make_session(client, professor_token, course["id"])

        # Activate first session
        first = await _patch_status(client, professor_token, session_a["id"], "active")
        assert first.status_code == 200

        # Try to activate second session while first is active
        second = await _patch_status(client, professor_token, session_b["id"], "active")
        assert second.status_code == 400
        assert second.json()["success"] is False

    async def test_student_cannot_change_status(
        self, client: AsyncClient, professor_token: str, student_token: str
    ):
        """Student (not professor or TA) cannot change session status → 403."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])

        res = await _patch_status(client, student_token, session["id"], "active")
        assert res.status_code == 403

    async def test_unauthenticated_status_change_rejected(
        self, client: AsyncClient, professor_token: str
    ):
        """No token → 401."""
        course = await _make_course(client, professor_token)
        session = await _make_session(client, professor_token, course["id"])
        res = await client.patch(
            f"{BASE}/{session['id']}/status",
            json={"status": "active"},
        )
        assert res.status_code == 401
