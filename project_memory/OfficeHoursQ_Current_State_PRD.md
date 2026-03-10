## OfficeHoursQ – Current State & Gap PRD

This document captures what the codebase currently implements vs. the main PRD, and outlines how to complete the remaining work. It is intentionally scoped to **v1** (auth, courses, sessions, questions/queue). For full behavioral details, the source of truth remains `OfficeHoursQ_PRD.md`.

---

### 1. High-Level Architecture (Current)

- **Frontend**
  - Next.js App Router (TypeScript) in `client/`.
  - Auth context (`AuthContext.tsx`) storing `{ user, token }` in memory and `token` in `localStorage`.
  - Pages implemented:
    - `/` – marketing/landing.
    - `/login`, `/register` – auth UI.
    - `/dashboard` – course list with create/join actions.
    - `/courses/[id]` – course detail + session list + create-session modal (professor only).
    - `/sessions/[id]` – combined student/TA session view with:
      - Student question submission & queue status panel.
      - TA queue list with claim/resolve/defer actions.
- **Backend**
  - FastAPI app in `server/app/main.py`.
  - Routers:
    - `health` – `/health`.
    - `auth` – `/auth/register`, `/auth/login`, `/auth/me`.
    - `courses` – `/courses`, `/courses/{id}`, `/courses/join`.
    - `sessions` – `/sessions`, `/sessions/{id}`, `/sessions/{id}/status`.
    - `questions` – `/questions` and the TA queue actions.
  - Auth:
    - Uses Supabase Auth for email/password.
    - Verifies access tokens via JWKS (RS256/ES256) using Supabase’s `/auth/v1/.well-known/jwks.json`, with HS256 fallback.
    - `decode_access_token` normalizes claims to `{ sub, role }`, pulling `role` from `user_metadata.role` when present.
  - Database:
    - Supabase Postgres via `supabase-py`.
    - `supabase` client created with **service role key** (RLS is permissive; FastAPI does auth/role checks).

---

### 2. Database Schema – What Exists

**Migration `001_initial_schema.sql` (canonical for v1)** – Creates:

- Enums:
  - `user_role (student|ta|professor)`
  - `enrollment_role (student|ta)`
- Tables:
  - `public.users`
    - `id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE`
    - `email TEXT UNIQUE NOT NULL`
    - `name TEXT NOT NULL`
    - `role user_role NOT NULL`
    - `created_at timestamptz default now()`
  - `public.courses`
    - `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
    - `name TEXT NOT NULL`
    - `invite_code TEXT UNIQUE NOT NULL`
    - `professor_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE`
    - `created_at timestamptz default now()`
  - `public.course_enrollments`
    - `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
    - `course_id UUID NOT NULL REFERENCES public.courses(id)`
    - `user_id UUID NOT NULL REFERENCES public.users(id)`
    - `role enrollment_role NOT NULL`
    - `joined_at timestamptz default now()`
    - `UNIQUE (course_id, user_id)`
- RLS:
  - Enabled on all three tables.
  - Permissive policies for now (mostly `SELECT USING (true)` etc.) so backend can enforce auth.
- Trigger:
  - `public.handle_new_user()` on `auth.users`:
    - On new Supabase Auth user, inserts into `public.users` with `id = auth.users.id`, `email`, `name`, `role` from `raw_user_meta_data`.

**Migration `002_core_sprint1_schema.sql`** – Adds:

- Additional enums: `session_status`, `question_status`, `question_priority`, `question_category`.
- Tables:
  - `public.sessions` (linked to `courses`).
  - `public.session_ta_assignments` (session ↔ TA many-to-many).
  - `public.questions` including:
    - Queue-related fields: `status`, `queue_position`, `claimed_by`, `claimed_at`, `deferred_at`, `resolved_at`, etc.
  - RLS enabled on all.
  - Very permissive RLS policies (anyone can select/insert/update/delete) – intended for dev; real restrictions are in FastAPI.

> **Current recommendation:** For v1, run **001 then 002** once on the Supabase project. Do not modify these tables manually; align backend to them (which it currently is).

---

### 3. Implemented Features vs. Original PRD

#### 3.1 Auth (Issues #3, #4)

**Implemented**

- `POST /auth/register`
  - Body: `{ email, password, name, role }`.
  - Calls `supabase.auth.sign_up` with `options.data = { name, role }`.
  - On success, returns `AuthResponse` with Supabase `session.access_token`.
- `POST /auth/login`
  - Body: `{ email, password }`.
  - Calls `supabase.auth.sign_in_with_password`.
  - Fetches canonical user row from `public.users` (fallback to `user_metadata`).
  - Returns `AuthResponse` with Supabase `access_token`.
- `GET /auth/me`
  - Uses decoded JWT (`sub`) to look up user in `public.users`.
  - Returns user profile (no token).
- Frontend:
  - `/register` and `/login` pages wired to these endpoints.
  - `AuthContext`:
    - Stores `{ user, token }`.
    - Persists `token` to `localStorage`.
    - On load, calls `/auth/me` with token to restore session.

**Gaps vs. PRD**

- Email confirmation:
  - Code assumes a session is returned at sign-up. If email confirmation is enabled in Supabase, this may not be true.
  - Currently returns a 400 with a generic message when `res.session` is missing.
- Rate limiting & lockout:
  - Not implemented (server-side DoS/brute-force protection).

**How to complete**

- Improve `register` to:
  - Detect “email confirmation required” and return a structured response the frontend can show (and possibly continue with a “Check your email” view).
- Add simple request rate limiting middleware (e.g., using a small in-memory or Redis-based counter) or rely on Supabase’s limits for now, documenting it explicitly if we stay with the current setup.

---

#### 3.2 Courses (Issue #5) & Dashboard (Issue #6)

**Implemented backend**

- `POST /courses` (create course, professor-only)
  - Dependency: `require_role("professor")`.
  - Generates 6-char alphanumeric invite code.
  - Inserts course row with `professor_id = user["sub"]`.
- `GET /courses`
  - Professors: courses where `professor_id = sub`.
  - Students/TAs: courses they’re enrolled in via `course_enrollments` join.
- `GET /courses/{course_id}`
  - Returns course if:
    - User is the course’s `professor_id`, or
    - User has a `course_enrollments` row for that course.
- `POST /courses/join`
  - Body: `{ invite_code }`.
  - Rejects professors.
  - Looks up course by `invite_code`, validates uniqueness in `course_enrollments`, inserts enrollment.

**Implemented frontend**

- `/dashboard`
  - Fetches courses using `GET /courses`.
  - Professor view:
    - “Create Course” modal → `POST /courses`.
    - Shows invite code for each course.
  - Student/TA view:
    - “Join Course” modal → `POST /courses/join`.
- `/courses/[id]`
  - Fetches:
    - `GET /courses/{id}` for course details.
    - `GET /sessions?course_id={id}` for sessions list.
  - Professors can create sessions from this page.

**Gaps / Edge Cases**

- Course update/delete endpoints are not implemented (not required for v1).
- No explicit RBAC on `list_sessions` (currently any enrolled user can see them; this matches PRD expectations).

**How to complete (if needed)**

- Add:
  - `PATCH /courses/{id}` and `DELETE /courses/{id}` with `require_role("professor")` and ownership check on `professor_id`.
  - Frontend actions in course detail page for renaming/deleting courses.

---

#### 3.3 Sessions (Issue #7)

**Implemented backend**

Router: `app/api/routes/sessions.py`

- `POST /sessions`
  - Auth: `require_role("professor")`.
  - Validates that the professor owns the course (`courses.professor_id = sub`).
  - Inserts into `public.sessions` with `status = 'scheduled'`.
  - Optionally inserts rows into `session_ta_assignments` when `ta_ids` are provided.
- `GET /sessions?course_id=...`
  - Lists all sessions for the course.
- `PUT /sessions/{session_id}`
  - Auth: `require_role("professor")`.
  - Only allowed when `status = 'scheduled'`.
  - Updates title/date/time and optionally TA assignments.
- `DELETE /sessions/{session_id}`
  - Auth: `require_role("professor")`.
  - Only allowed when `status = 'scheduled'`.
- `PATCH /sessions/{session_id}/status`
  - Auth: `require_role("professor", "ta")`.
  - Valid transitions:
    - `scheduled → active`:
      - Enforces “max one active session per course”.
    - `active → ended`:
      - Sets remaining non-resolved/non-withdrawn questions to a resolved-like state with `resolution_note = "Session ended without resolution"`.
  - Rejects any other status transitions.

**Implemented frontend**

- `/courses/[id]`
  - Lists sessions for the course with status chips (SCHEDULED/ACTIVE/ENDED).
  - Professors can create sessions via modal (calls `POST /sessions`).
- `/sessions/[id]`
  - Professor controls:
    - “Start” → `PATCH /sessions/{id}/status` with `status='active'`.
    - “End” → `PATCH /sessions/{id}/status` with `status='ended'`.
  - Students/TA see the session queue view (see below).

**Gaps vs. PRD**

- Session metadata in the session view:
  - We only fetch questions; the header uses generic text instead of real session title/time/course name.
  - There is no `GET /sessions/{id}` endpoint; questions list acts as the source of truth.
- TA assignment behavior:
  - Core DB structures exist, but we don’t yet use `session_ta_assignments` in authorization (e.g., restricting which TAs can manage which sessions).

**How to complete**

- Add `GET /sessions/{id}` returning session details + optional TAs.
- In `/sessions/[id]`:
  - Fetch session details alongside questions.
  - Render real session title, date/time, course name (via `courses` join or client-side fetch).
- Enforce TA assignment rules in `update_session_status` and `questions` actions if the PRD requires TAs to be explicitly assigned to a session.

---

#### 3.4 Questions & Queue (Issues #8, #9, #10)

**Implemented backend**

Router: `app/api/routes/questions.py`

- Helper: `recalculate_queue(session_id)`
  - Fetches all questions in `queued` or `in_progress` for the session, ordered by `queue_position`, and rewrites positions to `1..N`.
- `POST /questions`
  - Auth: `require_role("student")`.
  - Validates:
    - Session is `active`.
    - Student does not already have an active question (`queued` or `in_progress`) for that session.
  - Sets:
    - `status = 'queued'`.
    - `queue_position = current_active_count + 1`.
    - `student_id = sub`.
- `GET /questions?session_id=...`
  - Students: only their questions for the session, ordered by `queue_position`.
  - TAs/Professors: all questions for the session, joined to `users` for student/claimer name/email, ordered by `queue_position`.
- `GET /questions/{id}`
  - Students can only see their own question; staff can see any.
- `PUT /questions/{id}`
  - Auth: `require_role("student")`.
  - Only allowed while `status = 'queued'`.
  - Only the owning student can edit.
- `PATCH /questions/{id}/claim`
  - Auth: `require_role("ta", "professor")`.
  - Only allowed when `status = 'queued'`.
  - Sets:
    - `status = 'in_progress'`.
    - `claimed_by = sub`.
    - `claimed_at = now()`.
- `PATCH /questions/{id}/resolve`
  - Auth: `require_role("ta", "professor")`.
  - Only allowed when `status in ['queued', 'in_progress']`.
  - Sets:
    - `status = 'resolved'`.
    - `resolution_note` (from body).
    - `resolved_at = now()`.
    - `queue_position = -1` (removed from queue).
  - Calls `recalculate_queue` to compact the queue positions.
- `PATCH /questions/{id}/defer`
  - Auth: `require_role("ta", "professor")`.
  - Only allowed for `queued` or `in_progress` questions.
  - Logic:
    - Computes new position as `current_active_count + 1`.
    - Sets:
      - `status = 'queued'` **but** also sets `deferred_at` and updates `queue_position`.
    - Does **not** call `recalculate_queue` (assumes the manual bump to back is enough).
- `PATCH /questions/{id}/withdraw`
  - Auth: `require_role("student")`.
  - Only allowed for the owning student and `status in ['queued', 'in_progress']`.
  - Sets:
    - `status = 'withdrawn'`.
    - `queue_position = -1`.
  - Calls `recalculate_queue`.

**Implemented frontend**

- `/sessions/[id]`:
  - Fetches questions via `GET /questions?session_id=...`.
  - Student view:
    - Uses `QuestionSubmissionForm` component.
    - If student has an active question (`queued` or `in_progress`), shows queue status card with position and estimated wait (5 minutes per position).
    - Withdraw action calls `PATCH /questions/{id}/withdraw`.
  - TA/Professor view:
    - Shows queue ordered by `queue_position`.
    - Action buttons:
      - `Claim` → `PATCH /questions/{id}/claim`.
      - `Resolve` (only if claimed by current TA) → `PATCH /questions/{id}/resolve`.
      - `Defer` (Re-queue) → `PATCH /questions/{id}/defer`.

**Gaps vs. PRD**

- Queue logic details:
  - PRD specifies sort by `priority` then `submitted_at`, with `deferred` at back; current implementation primarily uses `queue_position` and relies on insertion order.
  - `defer` currently sets `status = 'queued'` but comments imply status might be `deferred`; this needs to be aligned with the PRD’s semantics and queries (`in_(['queued','in_progress'])`).
  - No real-time updates yet (polling every 10s instead of Supabase Realtime).
- Student editing:
  - UI has an “Edit” button but no form/modal to actually edit the question (even though backend supports `PUT /questions/{id}`).
- Helpful votes, analytics, notifications:
  - Not implemented; outside the current queue MVP.

**How to complete**

- Tighten queue semantics:
  - Store an explicit `submitted_at` (already in table) and use it in `recalculate_queue`:
    - Fetch active questions with appropriate sort (priority, then submitted_at, with `deferred` at back).
  - Decide on `status` semantics for deferred questions:
    - Either treat `deferred` as an active queue status and include it in the `in_([...])` filter, or keep `queued` with `deferred_at` purely as a marker.
- Add an edit modal to `QuestionSubmissionForm` when `activeQuestion` exists:
  - Load full question details on Edit.
  - Call `PUT /questions/{id}` with updated fields.
- Replace polling with Supabase Realtime or broadcast events later (for now, polling is acceptable but should be documented as a v1 compromise).

---

### 4. Not Implemented (But Mentioned in Original PRD)

These are deliberately **out of scope** or not yet started in the current code:

- Professor analytics dashboard (tabs, charts, TA performance).
- Helpful votes (`HelpfulVote` model) and knowledge base / similar questions search.
- Notifications system (`Notification` model).
- Real-time WebSockets / live updates via Supabase Realtime.
- Advanced edge cases:
  - Knowledge base search.
  - CSV export.
  - Recurring sessions beyond simple one-off sessions.

---

### 5. Recommended Next Steps

1. **Stabilize what’s built**
   - Ensure both migrations (`001`, `002`) are applied in the correct order on Supabase.
   - Confirm `handle_new_user` trigger exists and that new registrations create `public.users` rows.
   - Verify main flows end-to-end:
     - Register/Login as professor.
     - Course create/join.
     - Session create/start/end.
     - Student submit question, TA claim/resolve/defer/withdraw.

2. **Align queue behavior with PRD**
   - Formalize queue sort order and status semantics (`queued`, `in_progress`, `deferred`).
   - Adjust `recalculate_queue` and `defer` logic accordingly.

3. **Polish UX gaps**
   - Implement question edit modal.
   - Show real session/course names and times in `/sessions/[id]`.

4. **Plan analytics & notifications (future milestone)**
   - Use `OfficeHoursQ_PRD.md` as the source of truth for data models and endpoints.
   - Add separate routers (e.g., `/analytics`, `/notifications`) once queue/session flows are rock solid.

