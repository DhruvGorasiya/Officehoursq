# Issue #13 — Knowledge Base Search Endpoints Progress

## 1. Scope of Issue #13

**Goal:** Implement backend knowledge base APIs so students and staff can search resolved questions from past sessions for a given course.

GitHub issue: `#13 – Implement knowledge base search endpoints`

Acceptance criteria from PRD / issue:

- `GET /api/knowledge-base?course_id=X&search=Y&category=Z` returns **paginated** resolved questions (20/page).
- **Full-text search** across `title`, `description`, and `resolution_note`.
- Category filter works **independently** or **combined** with search.
- `GET /api/knowledge-base/similar?title=X&course_id=Y` returns **top 5 similar** resolved questions.
- Only **enrolled users** can access (403 otherwise).
- Results sorted by `helpful_votes` descending, then `resolved_at` descending.

This issue is **backend-only**; no frontend UI has been wired yet.

---

## 2. Database Changes (Migration 004)

**File:** `server/db_migrations/migrations/004_knowledge_base_search.sql`

### 2.1 Questions table updates

- Added `course_id UUID NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE`:
  - Initially nullable, then **backfilled** from `sessions.course_id`, then set `NOT NULL`.
- Added `helpful_votes INTEGER NOT NULL DEFAULT 0`:
  - Denormalized counter to support fast ordering by “most helpful”.
- Added `search_vector tsvector GENERATED ALWAYS AS (...) STORED`:
  - Computed as:
    - `to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'') || ' ' || coalesce(resolution_note,''))`
  - Used for full-text search across question title, description, and resolution note.

### 2.2 Helpful votes table

New table: `public.helpful_votes`

- Columns:
  - `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
  - `question_id UUID NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE`
  - `student_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE`
  - `created_at TIMESTAMPTZ DEFAULT now()`
  - **Unique constraint** on `(question_id, student_id)` (one vote per student per question).
- RLS policies (permissive, backend enforces auth):
  - `"Helpful votes are viewable by everyone"` (SELECT USING true)
  - `"Anyone can insert helpful votes"` (INSERT WITH CHECK true)
  - `"Anyone can delete helpful votes"` (DELETE USING true)

### 2.3 Indexes

- `idx_questions_search_vector`:
  - `CREATE INDEX ... USING GIN (search_vector);`
  - Supports fast full-text queries.
- `idx_questions_course_status`:
  - `CREATE INDEX ... ON public.questions (course_id, status);`
  - Matches common filters used by knowledge base queries.

### 2.4 RPC: find_similar_questions

New Postgres function:

- **Name:** `public.find_similar_questions(p_course_id UUID, p_title TEXT, p_limit INTEGER DEFAULT 5)`
- **Returns:** table with:
  - `id, title, description, category, resolution_note, helpful_votes, resolved_at, created_at, student_name, rank`
- **Logic:**
  - Uses `websearch_to_tsquery('english', p_title)` against `questions.search_vector`.
  - Filters to `course_id = p_course_id` and `status = 'resolved'`.
  - Joins `users` to expose `student_name`.
  - Orders by:
    - `ts_rank(search_vector, websearch_to_tsquery(...)) DESC`
    - `helpful_votes DESC`
    - `resolved_at DESC`
  - Limits to `p_limit` (default 5).

This function is invoked via Supabase `rpc` from the FastAPI route.

---

## 3. Backend API Changes

### 3.1 New router: `knowledge_base`

- **File:** `server/app/api/routes/knowledge_base.py`
- **Imported and registered in:** `server/app/main.py`

#### Enrollment helper

```python
def check_enrollment(user_id: str, role: str, course_id: str) -> bool:
    if role == "professor":
        res = (
            supabase.table("courses")
            .select("id")
            .eq("id", course_id)
            .eq("professor_id", user_id)
            .execute()
        )
        return bool(res.data)
    res = (
        supabase.table("course_enrollments")
        .select("id")
        .eq("course_id", course_id)
        .eq("user_id", user_id)
        .execute()
    )
    return bool(res.data)
```

- Reused by both endpoints to enforce:
  - Professors can always access their own courses.
  - Students/TAs must be enrolled via `course_enrollments`.
  - Non-enrolled users get `403` with message `"Not enrolled in this course"`.

#### Endpoint: `GET /api/v1/knowledge-base`

- **Purpose:** Paginated search of resolved questions for a course.
- **Query params:**
  - `course_id` (required)
  - `search` (optional full-text query)
  - `category` (optional filter)
  - `page` (optional, 1-indexed, default 1)
- **Core query:**
  - `status = 'resolved'`
  - `course_id = course_id`
  - Optional `.text_search("search_vector", search, options={"type": "websearch"})`
  - Optional `.eq("category", category)`
  - Order:
    - `helpful_votes DESC`
    - `resolved_at DESC`
  - Pagination:
    - `PAGE_SIZE = 20`
    - `.range(offset, offset + PAGE_SIZE - 1)` with `offset = (page - 1) * PAGE_SIZE`
  - Select fields:
    - `id, title, description, category, resolution_note, helpful_votes, resolved_at, created_at`
    - `student:users!questions_student_id_fkey(name)`
- **Response shape:**

```json
{
  "success": true,
  "data": [ /* resolved questions with student_name */ ],
  "page": 1,
  "page_size": 20,
  "total_count": 42
}
```

The route unwraps the joined `student` object into a flat `student_name` field.

#### Endpoint: `GET /api/v1/knowledge-base/similar`

- **Purpose:** Return top 5 similar resolved questions for a course given a title.
- **Query params:**
  - `course_id` (required)
  - `title` (required, `min_length=1`)
- **Flow:**
  1. Check enrollment with `check_enrollment`.
  2. Call Supabase RPC:
     - `supabase.rpc("find_similar_questions", {"p_course_id": course_id, "p_title": title, "p_limit": 5}).execute()`
  3. Return `{ "success": true, "data": res.data or [] }`.

The returned rows come directly from the Postgres function (including `rank`).

### 3.2 App registration

**File:** `server/app/main.py`

- Import updated to include the new router:

```python
from app.api.routes import health, auth, courses, sessions, questions, knowledge_base
```

- Router registration:

```python
app.include_router(
    knowledge_base.router,
    prefix=f"{settings.API_V1_PREFIX}/knowledge-base",
    tags=["knowledge-base"],
)
```

This exposes:

- `GET /api/v1/knowledge-base`
- `GET /api/v1/knowledge-base/similar`

---

## 4. Question Creation Changes

**File:** `server/app/api/routes/questions.py`

### 4.1 Denormalizing course_id on question create

In `create_question`:

- Session lookup was expanded from:
  - `select("status")`
- To:
  - `select("status, course_id")`

The question payload now includes `course_id` from the session:

```python
q_data = req.model_dump()
q_data["student_id"] = student_id
q_data["course_id"] = session_res.data["course_id"]
q_data["status"] = "queued"
q_data["queue_position"] = queue_pos
```

**Impact:**

- New questions automatically carry `course_id`, aligning with the PRD data model.
- Knowledge base queries can efficiently filter by `course_id` without joining `sessions`.

---

## 5. Schemas

**File:** `server/app/schemas/knowledge_base.py`

- Response models for documentation / future use (not yet wired into FastAPI response models, but reflect expected shapes):
  - `KnowledgeBaseItem`:
    - `id`, `title`, `description`, `category`, `resolution_note?`, `helpful_votes`, `resolved_at?`, `created_at`, `student_name?`
  - `SimilarQuestionItem`:
    - Same fields plus optional `rank` field from the Postgres function.

These mirror the columns returned by the main search query and the `find_similar_questions` RPC.

---

## 6. Testing Summary (Backend)

After applying migration `004_knowledge_base_search.sql` to Supabase and rebuilding the backend:

- **App load:**
  - `python -c "from app.main import app; print('App loaded OK')"` succeeds.
  - Routes list includes:
    - `/api/v1/knowledge-base [GET]`
    - `/api/v1/knowledge-base/similar [GET]`
- **Lints:**
  - `ReadLints` on `main.py`, `questions.py`, `knowledge_base.py`, `knowledge_base.py` (schemas) shows **no errors**.

### 6.1 Manual HTTP tests (suggested)

- Obtain a valid JWT for an enrolled user.
- Call:

```bash
curl "http://localhost:8000/api/v1/knowledge-base?course_id=COURSE_ID" \
  -H "Authorization: Bearer TOKEN"
```

- Then with filters:

```bash
curl "http://localhost:8000/api/v1/knowledge-base?course_id=COURSE_ID&search=timeout%20error&category=debugging&page=2" \
  -H "Authorization: Bearer TOKEN"
```

- And for similar questions:

```bash
curl "http://localhost:8000/api/v1/knowledge-base/similar?course_id=COURSE_ID&title=Recursion stack overflow" \
  -H "Authorization: Bearer TOKEN"
```

**Expected:**

- Enrolled user:
  - `200` with `success: true` and data matching filters.
- Non-enrolled user:
  - `403` with `"Not enrolled in this course"`.

---

## 7. Frontend Status & Next Steps

- No UI components currently consume these endpoints.
- Existing session/question views remain unchanged and continue to function.

**Next suggested steps (future issue):**

- Add a **similar questions panel** above the student submission form that:
  - Calls `GET /api/v1/knowledge-base/similar` as the user types the title.
  - Shows top 5 matching resolved questions in a cyan-tinted card as described in the PRD.
- Add a **course-level knowledge base page** (e.g., `/courses/[id]/knowledge-base`) that:
  - Calls `GET /api/v1/knowledge-base` with pagination, filters, and search.
  - Reuses existing card visual language for resolved questions.

