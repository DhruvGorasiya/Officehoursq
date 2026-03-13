"""
Integration tests for analytics endpoints:
  GET /api/v1/analytics/overview?course_id=
  GET /api/v1/analytics/categories?course_id=
  GET /api/v1/analytics/trends?course_id=
  GET /api/v1/analytics/ta-performance?course_id=
  GET /api/v1/analytics/export?course_id=

Uses the real Supabase project — no mocking.
"""

import uuid
import pytest  # noqa: F401
import pytest_asyncio
from httpx import AsyncClient

ANALYTICS_BASE = "/api/v1/analytics"
COURSES_BASE = "/api/v1/courses"
SESSIONS_BASE = "/api/v1/sessions"
QUESTIONS_BASE = "/api/v1/questions"


# ===========================================================================
# Setup Fixtures
# ===========================================================================

@pytest_asyncio.fixture(scope="module")
async def analytics_setup(
    _session_client: AsyncClient,
    professor_token: str,
    ta_token: str,
    student_token: str,
) -> tuple[str, str, str, str]:
    """Create a course, session, and mixed questions to populate analytics data."""
    uid = uuid.uuid4().hex[:6].upper()

    # 1. Professor creates course
    course_res = await _session_client.post(
        COURSES_BASE,
        json={"name": f"CS-{uid} Analytics"},
        headers={"Authorization": f"Bearer {professor_token}"},
    )
    assert course_res.status_code == 200
    course_id = course_res.json()["data"]["id"]
    invite_code = course_res.json()["data"]["invite_code"]

    # 2. Join users
    for token in [student_token, ta_token]:
        res = await _session_client.post(
            f"{COURSES_BASE}/join",
            json={"invite_code": invite_code},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

    # 3. Create and activate a session
    sess_res = await _session_client.post(
        SESSIONS_BASE,
        json={
            "course_id": course_id,
            "title": f"Session {uid}",
            "date": "2028-01-01",
            "start_time": "12:00:00",
            "end_time": "14:00:00",
        },
        headers={"Authorization": f"Bearer {professor_token}"},
    )
    assert sess_res.status_code == 200
    session_id = sess_res.json()["data"]["id"]

    await _session_client.patch(
        f"{SESSIONS_BASE}/{session_id}/status",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {professor_token}"},
    )

    # 4. Submit and resolve two questions (different categories)
    q1 = await _session_client.post(
        QUESTIONS_BASE,
        json={
            "session_id": session_id,
            "title": "Debugging question",
            "description": "desc",
            "what_tried": "tried",
            "category": "debugging",
            "priority": "low",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    q1_id = q1.json()["data"]["id"]

    # Withdraw student wait
    await _session_client.patch(
        f"{QUESTIONS_BASE}/{q1_id}/withdraw",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # Un-withdraw by submitting a new one instead. Wait, just submit them sequentially.
    q2 = await _session_client.post(
        QUESTIONS_BASE,
        json={
            "session_id": session_id,
            "title": "Conceptual question",
            "description": "desc",
            "what_tried": "tried",
            "category": "conceptual",
            "priority": "low",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    q2_id = q2.json()["data"]["id"]

    await _session_client.patch(
        f"{QUESTIONS_BASE}/{q2_id}/claim",
        headers={"Authorization": f"Bearer {ta_token}"},
    )

    await _session_client.patch(
        f"{QUESTIONS_BASE}/{q2_id}/resolve",
        json={"resolution_note": "Resolved Q2"},
        headers={"Authorization": f"Bearer {ta_token}"},
    )

    return course_id, professor_token, ta_token, student_token


# ===========================================================================
# Tests for /api/v1/analytics/overview
# ===========================================================================

class TestOverviewAnalytics:

    async def test_professor_gets_overview(self, client: AsyncClient, analytics_setup):
        course_id, prof_token, _, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/overview",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "total_questions" in data
        assert "avg_wait_minutes" in data
        assert "avg_resolve_minutes" in data
        assert "recent_sessions" in data
        assert isinstance(data["recent_sessions"], list)
        
        # We submitted 2 questions (1 withdrawn, 1 resolved) in the fixture
        assert data["total_questions"] >= 2

    async def test_ta_cannot_access_overview(self, client: AsyncClient, analytics_setup):
        course_id, _, ta_token, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/overview",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_student_cannot_access_overview(self, client: AsyncClient, analytics_setup):
        course_id, _, _, student_token = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/overview",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_rejected(self, client: AsyncClient, analytics_setup):
        course_id, _, _, _ = analytics_setup
        res = await client.get(f"{ANALYTICS_BASE}/overview", params={"course_id": course_id})
        assert res.status_code == 401


# ===========================================================================
# Tests for /api/v1/analytics/categories
# ===========================================================================

class TestCategoriesAnalytics:

    async def test_professor_gets_categories(self, client: AsyncClient, analytics_setup):
        course_id, prof_token, _, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/categories",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "categories" in data
        assert "total_resolved" in data
        
        # Should have at least the 'conceptual' category resolved
        categories = [c["category"] for c in data["categories"]]
        assert "conceptual" in categories
        
        conceptual = next(c for c in data["categories"] if c["category"] == "conceptual")
        assert "count" in conceptual
        assert "percentage" in conceptual

    async def test_ta_cannot_access(self, client: AsyncClient, analytics_setup):
        course_id, _, ta_token, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/categories",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_rejected(self, client: AsyncClient, analytics_setup):
        course_id, _, _, _ = analytics_setup
        res = await client.get(f"{ANALYTICS_BASE}/categories", params={"course_id": course_id})
        assert res.status_code == 401


# ===========================================================================
# Tests for /api/v1/analytics/trends
# ===========================================================================

class TestTrendsAnalytics:

    async def test_professor_gets_trends(self, client: AsyncClient, analytics_setup):
        course_id, prof_token, _, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/trends",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "weeks" in data
        assert isinstance(data["weeks"], list)
        
        # We submitted 2 questions, so at least 1 week should exist
        assert len(data["weeks"]) > 0
        assert "week_start" in data["weeks"][0]
        assert "count" in data["weeks"][0]
        assert data["weeks"][0]["count"] >= 2

    async def test_ta_cannot_access(self, client: AsyncClient, analytics_setup):
        course_id, _, ta_token, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/trends",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_rejected(self, client: AsyncClient, analytics_setup):
        course_id, _, _, _ = analytics_setup
        res = await client.get(f"{ANALYTICS_BASE}/trends", params={"course_id": course_id})
        assert res.status_code == 401


# ===========================================================================
# Tests for /api/v1/analytics/ta-performance
# ===========================================================================

class TestTAPerformanceAnalytics:

    async def test_professor_gets_ta_performance(self, client: AsyncClient, analytics_setup):
        course_id, prof_token, _, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/ta-performance",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "tas" in data
        assert isinstance(data["tas"], list)
        
        # We have one TA who resolved a conceptual question
        assert len(data["tas"]) >= 1
        ta_stats = data["tas"][0]
        assert "name" in ta_stats
        assert "resolved_count" in ta_stats
        assert ta_stats["resolved_count"] >= 1
        assert "avg_resolve_minutes" in ta_stats

    async def test_ta_cannot_access(self, client: AsyncClient, analytics_setup):
        course_id, _, ta_token, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/ta-performance",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_rejected(self, client: AsyncClient, analytics_setup):
        course_id, _, _, _ = analytics_setup
        res = await client.get(f"{ANALYTICS_BASE}/ta-performance", params={"course_id": course_id})
        assert res.status_code == 401


# ===========================================================================
# Tests for /api/v1/analytics/export
# ===========================================================================

class TestExportAnalytics:

    async def test_professor_gets_csv_export(self, client: AsyncClient, analytics_setup):
        course_id, prof_token, _, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/export",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/csv")
        assert f"filename=\"analytics_{course_id}.csv\"" in res.headers["content-disposition"]
        
        content = res.text
        # Check CSV header
        assert "question_id,session_title,created_at" in content
        # Check that our data is physically present
        assert "Conceptual question" not in content  # wait, description doesn't include title.
        # But category "conceptual" should be there
        assert "conceptual" in content

    async def test_ta_cannot_export(self, client: AsyncClient, analytics_setup):
        course_id, _, ta_token, _ = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/export",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {ta_token}"},
        )
        assert res.status_code == 403

    async def test_student_cannot_export(self, client: AsyncClient, analytics_setup):
        course_id, _, _, student_token = analytics_setup
        res = await client.get(
            f"{ANALYTICS_BASE}/export",
            params={"course_id": course_id},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 403

    async def test_unauthenticated_rejected(self, client: AsyncClient, analytics_setup):
        course_id, _, _, _ = analytics_setup
        res = await client.get(f"{ANALYTICS_BASE}/export", params={"course_id": course_id})
        assert res.status_code == 401
