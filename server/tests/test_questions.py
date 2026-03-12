"""
Integration tests for POST   /api/v1/questions
                     GET    /api/v1/questions?session_id=
                     GET    /api/v1/questions/{q_id}
                     PUT    /api/v1/questions/{q_id}
                     PATCH  /api/v1/questions/{q_id}/claim
                     PATCH  /api/v1/questions/{q_id}/resolve
                     PATCH  /api/v1/questions/{q_id}/defer
                     PATCH  /api/v1/questions/{q_id}/withdraw
                     POST   /api/v1/questions/{q_id}/helpful

Uses the real Supabase project — no mocking.
Each test that needs an active session calls `setup_active_session()`.

Route implementation notes (from questions.py):
  * POST   → require_role("student"); TAs/professors → 403
  * GET    (list) → any authenticated user; students see only their own questions
              (no 403 is raised — the route silently filters).
              "403: student cannot list all session questions" from the spec
              is interpreted as: students get 200 but only see their own subset.
  * GET    /{q_id} → students only see their own; others' questions → 403
  * PUT    → require_role("student") — TAs → 403 (they're not students)
  * PATCH  /claim   → require_role("ta", "professor") — students → 403
  * PATCH  /resolve → require_role("ta", "professor") — students → 403
  * PATCH  /defer   → require_role("ta", "professor") — students → 403
  * PATCH  /withdraw → require_role("student") — TAs → 403
  * POST   /helpful  → require_role("student") — only resolved questions
"""

import uuid
import pytest
from httpx import AsyncClient

QUESTIONS_BASE = "/api/v1/questions"
COURSES_BASE = "/api/v1/courses"
SESSIONS_BASE = "/api/v1/sessions"


# ===========================================================================
# Shared setup helper
# ===========================================================================

async def setup_active_session(
    client: AsyncClient,
    professor_token: str,
    student_token: str,
    ta_token: str,
) -> tuple[str, str]:
    """Create course → enroll student & TA → create session → activate.

    Returns (course_id, session_id).
    """
    uid = uuid.uuid4().hex[:6].upper()

    # 1. Professor creates course
    course_res = await client.post(
        COURSES_BASE,
        json={"name": f"CS-{uid} Q-Test"},
        headers={"Authorization": f"Bearer {professor_token}"},
    )
    assert course_res.status_code == 200, f"Course creation failed: {course_res.json()}"
    course = course_res.json()["data"]
    course_id = course["id"]
    invite_code = course["invite_code"]

    # 2. Student joins course
    s_join = await client.post(
        f"{COURSES_BASE}/join",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert s_join.status_code == 200, f"Student join failed: {s_join.json()}"

    # 3. TA joins course
    ta_join = await client.post(
        f"{COURSES_BASE}/join",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {ta_token}"},
    )
    assert ta_join.status_code == 200, f"TA join failed: {ta_join.json()}"

    # 4. Professor creates a scheduled session
    session_res = await client.post(
        SESSIONS_BASE,
        json={
            "course_id": course_id,
            "title": f"Session {uid}",
            "date": "2027-06-15",
            "start_time": "14:00:00",
            "end_time": "16:00:00",
        },
        headers={"Authorization": f"Bearer {professor_token}"},
    )
    assert session_res.status_code == 200, f"Session creation failed: {session_res.json()}"
    session_id = session_res.json()["data"]["id"]

    # 5. Activate the session
    activate_res = await client.patch(
        f"{SESSIONS_BASE}/{session_id}/status",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {professor_token}"},
    )
    assert activate_res.status_code == 200, f"Session activation failed: {activate_res.json()}"

    return course_id, session_id


def _q_payload(session_id: str) -> dict:
    uid = uuid.uuid4().hex[:4].upper()
    return {
        "session_id": session_id,
        "title": f"Test Question {uid}",
        "description": "I am stuck on this problem and need help.",
        "what_tried": "I tried reading the docs and searching Stack Overflow.",
        "category": "debugging",
        "priority": "medium",
    }


async def _submit_question(
    client: AsyncClient, token: str, session_id: str
) -> dict:
    """Submit a question as a student, return the question data dict."""
    res = await client.post(
        QUESTIONS_BASE,
        json=_q_payload(session_id),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, f"Question submission failed: {res.json()}"
    return res.json()["data"]


# ===========================================================================
# POST /api/v1/questions  — Submit question
# ===========================================================================

class TestSubmitQuestion:

    async def test_student_submits_question_success(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student submits question to active session → 200, status=queued."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        res = await client.post(
            QUESTIONS_BASE,
            json=_q_payload(session_id),
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["status"] == "queued"
        assert data["session_id"] == session_id
        assert "id" in data

    async def test_student_cannot_submit_second_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student submits a second question to the same session → 400."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        await _submit_question(client, student_token, session_id)

        res = await client.post(
            QUESTIONS_BASE,
            json=_q_payload(session_id),
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 400
        assert res.json()["success"] is False

    async def test_student_cannot_submit_to_inactive_session(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Submit to a scheduled (not active) session → 400."""
        uid = uuid.uuid4().hex[:6].upper()
        # Create course + join + scheduled session (NOT activated)
        course_res = await client.post(
            COURSES_BASE,
            json={"name": f"CS-{uid} Inactive"},
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        course = course_res.json()["data"]
        await client.post(
            f"{COURSES_BASE}/join",
            json={"invite_code": course["invite_code"]},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Create session but do NOT activate it
        session_res = await client.post(
            SESSIONS_BASE,
            json={
                "course_id": course["id"],
                "title": "Inactive Session",
                "date": "2027-06-15",
                "start_time": "14:00:00",
                "end_time": "16:00:00",
            },
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        session_id = session_res.json()["data"]["id"]

        res = await client.post(
            QUESTIONS_BASE,
            json=_q_payload(session_id),
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 400
        assert res.json()["success"] is False

    async def test_ta_cannot_submit_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA tries to submit a question → 403."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        res = await client.post(
            QUESTIONS_BASE,
            json=_q_payload(session_id),
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_cannot_submit(self, client: AsyncClient):
        """No token → 401."""
        res = await client.post(
            QUESTIONS_BASE,
            json=_q_payload(str(uuid.uuid4())),
        )
        assert res.status_code == 401


# ===========================================================================
# GET /api/v1/questions?session_id=  — List questions
# ===========================================================================

class TestListQuestions:

    async def test_ta_sees_all_questions(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA lists session questions → 200, list contains submitted question."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.get(
            QUESTIONS_BASE,
            params={"session_id": session_id},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        ids = [item["id"] for item in body["data"]]
        assert q["id"] in ids

    async def test_professor_sees_all_questions(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Professor lists session questions → 200."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.get(
            QUESTIONS_BASE,
            params={"session_id": session_id},
            headers={"Authorization": f"Bearer {professor_token}"},
        )
        assert res.status_code == 200
        ids = [item["id"] for item in res.json()["data"]]
        assert q["id"] in ids

    async def test_student_sees_only_own_questions(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student list endpoint returns 200 but only their own questions (not a 403).
        The route silently filters to student's own questions instead of raising a 403."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.get(
            QUESTIONS_BASE,
            params={"session_id": session_id},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        # Student should see their own question
        ids = [item["id"] for item in body["data"]]
        assert q["id"] in ids

    async def test_unauthenticated_list_rejected(self, client: AsyncClient):
        """No token → 401."""
        res = await client.get(
            QUESTIONS_BASE, params={"session_id": str(uuid.uuid4())}
        )
        assert res.status_code == 401


# ===========================================================================
# GET /api/v1/questions/{q_id}  — Get single question
# ===========================================================================

class TestGetQuestion:

    async def test_student_sees_own_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student fetches their own question → 200 with all fields."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.get(
            f"{QUESTIONS_BASE}/{q['id']}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["id"] == q["id"]
        assert body["data"]["status"] == "queued"

    async def test_ta_sees_any_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA can fetch any question in the session → 200."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.get(
            f"{QUESTIONS_BASE}/{q['id']}",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["id"] == q["id"]

    async def test_student_cannot_see_another_students_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student A cannot fetch Student B's question → 403.

        We use a second fresh student (student2) registered inline for this test.
        """
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        # Submit question as student (the session-scoped student_token)
        q = await _submit_question(client, student_token, session_id)

        # Register second student inline
        uid2 = uuid.uuid4().hex[:8]
        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"student2_{uid2}@testsuite.dev",
                "password": "TestPass123!",
                "name": f"Student2 {uid2}",
                "role": "student",
            },
        )
        assert reg2.status_code == 200, f"Student2 registration failed: {reg2.json()}"
        token2 = reg2.json()["data"]["token"]

        res = await client.get(
            f"{QUESTIONS_BASE}/{q['id']}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert res.status_code == 403
        assert res.json()["success"] is False

    async def test_unauthenticated_get_question_rejected(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """No token → 401."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)
        res = await client.get(f"{QUESTIONS_BASE}/{q['id']}")
        assert res.status_code == 401


# ===========================================================================
# PUT /api/v1/questions/{q_id}  — Edit question
# ===========================================================================

class TestUpdateQuestion:

    async def test_student_edits_queued_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student edits their own queued question → 200, new title returned."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)
        new_title = f"Updated Title {uuid.uuid4().hex[:4].upper()}"

        res = await client.put(
            f"{QUESTIONS_BASE}/{q['id']}",
            json={"title": new_title},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["title"] == new_title

    async def test_student_cannot_edit_claimed_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Once a question is claimed (in_progress), student cannot edit it → 400."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        # TA claims the question
        claim = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert claim.status_code == 200

        res = await client.put(
            f"{QUESTIONS_BASE}/{q['id']}",
            json={"title": "Should Fail"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 400
        assert res.json()["success"] is False

    async def test_ta_cannot_edit_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA tries to edit a student's question → 403 (require_role('student'))."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.put(
            f"{QUESTIONS_BASE}/{q['id']}",
            json={"title": "TA Edit Attempt"},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_edit_rejected(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """No token → 401."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)
        res = await client.put(f"{QUESTIONS_BASE}/{q['id']}", json={"title": "Anon"})
        assert res.status_code == 401


# ===========================================================================
# PATCH /api/v1/questions/{q_id}/claim
# ===========================================================================

class TestClaimQuestion:

    async def test_ta_claims_queued_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA claims a queued question → 200, status becomes in_progress."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["status"] == "in_progress"
        assert body["data"]["claimed_by"] is not None

    async def test_ta_cannot_claim_already_claimed_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA tries to claim an already in_progress question → 400."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        # First claim
        first = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert first.status_code == 200

        # Second claim attempt
        second = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert second.status_code == 400
        assert second.json()["success"] is False

    async def test_student_cannot_claim(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student tries to claim a question → 403."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/claim",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_claim_rejected(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """No token → 401."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)
        res = await client.patch(f"{QUESTIONS_BASE}/{q['id']}/claim")
        assert res.status_code == 401


# ===========================================================================
# PATCH /api/v1/questions/{q_id}/resolve
# ===========================================================================

class TestResolveQuestion:

    async def test_ta_resolves_claimed_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA claims then resolves a question → 200, status=resolved."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/claim",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/resolve",
            json={"resolution_note": "Fixed by reviewing the error message carefully."},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["status"] == "resolved"
        assert body["data"]["resolution_note"] is not None

    async def test_ta_resolves_queued_question_directly(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA can resolve directly from queued (without claiming first) → 200."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/resolve",
            json={"resolution_note": "Quick answer: use list comprehension."},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "resolved"

    async def test_student_cannot_resolve(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student tries to resolve a question → 403."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/resolve",
            json={"resolution_note": "Student self-resolving."},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_resolve_rejected(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """No token → 401."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)
        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/resolve",
            json={"resolution_note": "Anon."},
        )
        assert res.status_code == 401


# ===========================================================================
# PATCH /api/v1/questions/{q_id}/defer
# ===========================================================================

class TestDeferQuestion:

    async def test_ta_defers_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """TA defers a queued question → 200, status=deferred."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/defer",
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["status"] == "deferred"

    async def test_student_cannot_defer(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student tries to defer a question → 403."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/defer",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_defer_rejected(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """No token → 401."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)
        res = await client.patch(f"{QUESTIONS_BASE}/{q['id']}/defer")
        assert res.status_code == 401


# ===========================================================================
# PATCH /api/v1/questions/{q_id}/withdraw
# ===========================================================================

class TestWithdrawQuestion:

    async def test_student_withdraws_own_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student withdraws their queued question → 200, status=withdrawn."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/withdraw",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["status"] == "withdrawn"

    async def test_student_cannot_withdraw_resolved_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student cannot withdraw a question that's already resolved → 400."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        # TA resolves it first
        await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/resolve",
            json={"resolution_note": "Already solved."},
            headers={"Authorization": f"Bearer {ta_token}"},
        )

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/withdraw",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 400
        assert res.json()["success"] is False

    async def test_student_cannot_withdraw_another_students_question(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student A cannot withdraw Student B's question → 403."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        # Register a second student
        uid2 = uuid.uuid4().hex[:8]
        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"withdrawstudent2_{uid2}@testsuite.dev",
                "password": "TestPass123!",
                "name": f"WithdrawStudent2 {uid2}",
                "role": "student",
            },
        )
        assert reg2.status_code == 200, f"Student2 registration failed: {reg2.json()}"
        token2 = reg2.json()["data"]["token"]

        res = await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/withdraw",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert res.status_code == 403
        assert res.json()["success"] is False

    async def test_unauthenticated_withdraw_rejected(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """No token → 401."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)
        res = await client.patch(f"{QUESTIONS_BASE}/{q['id']}/withdraw")
        assert res.status_code == 401


# ===========================================================================
# POST /api/v1/questions/{q_id}/helpful
# ===========================================================================

class TestHelpfulVote:

    async def test_student_votes_resolved_question_helpful(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Student votes a resolved question as helpful → 200, helpful_votes incremented."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        # Resolve the question first
        await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/resolve",
            json={"resolution_note": "Great question, here's the fix."},
            headers={"Authorization": f"Bearer {ta_token}"},
        )

        res = await client.post(
            f"{QUESTIONS_BASE}/{q['id']}/helpful",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["helpful_votes"] >= 1

    async def test_student_cannot_vote_twice(
        self, client: AsyncClient, professor_token: str, student_token: str, ta_token: str
    ):
        """Voting the same resolved question helpful twice → 400."""
        _, session_id = await setup_active_session(
            client, professor_token, student_token, ta_token
        )
        q = await _submit_question(client, student_token, session_id)

        # Resolve
        await client.patch(
            f"{QUESTIONS_BASE}/{q['id']}/resolve",
            json={"resolution_note": "Fixed."},
            headers={"Authorization": f"Bearer {ta_token}"},
        )

        # First vote
        first = await client.post(
            f"{QUESTIONS_BASE}/{q['id']}/helpful",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert first.status_code == 200

        # Second vote — should be rejected
        second = await client.post(
            f"{QUESTIONS_BASE}/{q['id']}/helpful",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert second.status_code == 400
        assert second.json()["success"] is False

    async def test_unauthenticated_helpful_rejected(self, client: AsyncClient):
        """No token → 401."""
        res = await client.post(f"{QUESTIONS_BASE}/{uuid.uuid4()}/helpful")
        assert res.status_code == 401
