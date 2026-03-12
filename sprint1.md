# OfficeHoursQ — Sprint 1 Comprehensive Documentation

This document captures the complete state of **Sprint 1** for the OfficeHoursQ project: repository layout, files and folders, code structure, and what has been implemented. It is based on the current codebase plus the detailed setup log in `SETUP_IMPLEMENTATION_LOG.md` and the project PRD.

---

## 1. Sprint 1 Scope

**Sprint 1 GitHub issues:**

- #1: Set up project monorepo and dev environment
- #2: Set up database schema and migrations (now implemented with PostgreSQL migrations under `server/db_migrations`)
- #3: Implement auth endpoints (register, login, me)
- #4: Build auth UI (register, login pages)
- #5: Implement course CRUD and join endpoints
- #6: Build course dashboard UI
- #7: Implement session CRUD and status management endpoints
- #8: Implement question submission and retrieval endpoints
- #9: Build student question submission form UI
- #10: Implement TA queue actions (claim, resolve, defer)

Sprint 1 focuses on **core auth, course/session/question flows, and initial UI** so that a basic version of OfficeHoursQ works end-to-end for all three roles.

---

## 2. Monorepo Layout (Sprint 1)

Root directory (relevant to Sprint 1):

- `.gitignore` — ignores Node, Python, env, build, and IDE files.
- `.cursorrules` — project-wide rules and constraints (source of truth for stack and behavior).
- `README.md` — high-level overview, stack, and basic setup.
- `SETUP_IMPLEMENTATION_LOG.md` — detailed chronological log of environment and initial setup.
- `sprint1.md` — this document.
- `project_memory/`
  - `OfficeHoursQ_PRD.md` — product requirements (authoritative behavior).
  - `OfficeHoursQ_Current_State_PRD.md` — snapshot of current implementation vs PRD.
  - `Mockup.jsx` — UI mockup as JSX.
- `client/` — React (Vite-like structure adapted to PRD; currently Next-style app directory but used as the client).
- `server/` — FastAPI-style Python backend with PostgreSQL and migrations (superseding the earlier Supabase approach).

High‑level tree (only Sprint-1‑relevant files shown):

- `client/`
  - `.env.example`
  - `.gitignore`
  - `package.json`, `package-lock.json`
  - `next.config.ts`, `tsconfig.json`, `postcss.config.mjs`
  - `eslint.config.mjs`
  - `public/` (static assets)
  - `src/`
    - `app/`
      - `favicon.ico`
      - `globals.css`
      - `layout.tsx`
      - `page.tsx` (root landing/dashboard entry)
      - `(auth)/`
        - `login/page.tsx`
        - `register/page.tsx`
      - `dashboard/page.tsx`
      - `courses/[id]/page.tsx`
      - `sessions/[id]/page.tsx`
    - `components/`
      - `common/NavBar.tsx`
      - `questions/QuestionSubmissionForm.tsx`
    - `context/AuthContext.tsx`
  - `README.md` (client-specific)

- `server/`
  - `.env.example`
  - `requirements.txt`
  - `app/`
    - `__init__.py`
    - `main.py`
    - `core/`
      - `__init__.py`
      - `config.py`
      - `database.py`
      - `deps.py`
      - `security.py`
    - `api/`
      - `__init__.py`
      - `routes/`
        - `__init__.py`
        - `health.py`
        - `auth.py`
        - `courses.py`
        - `sessions.py`
        - `questions.py`
    - `models/`
      - `__init__.py` (SQLAlchemy/Postgres models to be attached or generated from migrations)
    - `schemas/`
      - `__init__.py`
      - `common.py`
      - `auth.py`
      - `courses.py`
      - `sessions.py`
      - `questions.py`
    - `services/`
      - `__init__.py`
  - `db_migrations/`
    - `migrations/`
      - `001_initial_schema.sql`
      - `002_core_sprint1_schema.sql`
      - `003_add_unresolved_status.sql`

This structure satisfies Sprint 1’s requirement for a monorepo with a separate client and server, and a database schema managed through migrations.

---

## 3. Backend (Server) — Sprint 1 Code Structure

### 3.1 Core Configuration & Infrastructure

- `server/requirements.txt`  
  Contains all backend dependencies for Sprint 1:
  - FastAPI, uvicorn
  - pydantic with email support (`pydantic[email]`), pydantic-settings
  - `python-dotenv`, `httpx`, `python-multipart`
  - `python-jose[cryptography]` for JWT
  - `bcrypt` for password hashing

- `server/app/core/config.py`  
  - Pydantic `Settings` class reads environment variables from `.env`:
    - Database connection URL (PostgreSQL)
    - JWT secret, algorithm, expiration
    - CORS origins
    - Project name and API prefix (`/api` or `/api/v1` depending on configuration).
  - Exposes a singleton `settings` instance used across the app.

- `server/app/core/database.py`  
  - Sets up the database connection (PostgreSQL) for FastAPI:
    - Either via an async engine + session factory (SQLAlchemy) or a lightweight connection utility, depending on final implementation in migrations.
  - This underpins all Sprint 1 CRUD endpoints (auth, courses, sessions, questions).

- `server/app/core/security.py`  
  - Password hashing and verification using `bcrypt`:
    - `hash_password(plain: str) -> str`
    - `verify_password(plain: str, hashed: str) -> bool`
  - JWT utilities using `python-jose`:
    - `create_access_token(data: dict, expires_delta: timedelta | None) -> str`
    - `decode_access_token(token: str) -> dict` (raises on invalid/expired token)

- `server/app/core/deps.py`  
  - Common dependencies for FastAPI routes:
    - Reusable HTTPBearer dependency for reading the `Authorization: Bearer ...` header.
    - `get_current_user`:
      - Decodes JWT, loads the user from DB, injects into route handlers.
      - Raises 401 for missing/invalid/expired tokens.
    - `require_role(*roles)`:
      - Role-based guard: ensures `current_user.role` is in allowed roles.
      - Raises 403 otherwise.

### 3.2 Schemas (Pydantic Models)

All schemas follow the PRD; key ones for Sprint 1:

- `server/app/schemas/common.py`
  - `SuccessResponse[T]`: standard `{ success: true, data: T }` wrapper.
  - `ErrorResponse`: `{ success: false, message: str }`.

- `server/app/schemas/auth.py`
  - `UserRole` enum: `student`, `ta`, `professor`.
  - `RegisterRequest`:
    - `email: EmailStr`, `password: str`, `name: str`, `role: UserRole`.
  - `LoginRequest`:
    - `email: EmailStr`, `password: str`.
  - `AuthResponse`:
    - `access_token`, `token_type`, `user` payload (id, email, name, role).

- `server/app/schemas/courses.py`
  - Course and enrollment models aligned with PRD:
    - `CourseCreate`, `CourseResponse`
    - `CourseEnrollmentResponse` (role, joined_at)
  - Each maps closely to the database fields defined in `001`/`002` migrations.

- `server/app/schemas/sessions.py`
  - `SessionStatus` enum: `scheduled`, `active`, `ended`.
  - `SessionCreate`, `SessionUpdate`, `SessionResponse`.
  - Includes fields for `course_id`, title, date, time window, topics, recurrence flags, and TA assignments.

- `server/app/schemas/questions.py`
  - Enums for `QuestionStatus`, `QuestionCategory`, `QuestionPriority`.
  - `QuestionCreate`:
    - All main question fields from the PRD (title, description, code_snippet, error_message, what_tried, category, priority, session_id, course_id).
  - `QuestionUpdate` (for queued-only edits).
  - `QuestionResponse` with status, timestamps (submitted_at, claimed_at, resolved_at, deferred_at), and queue-position-related fields where needed.

### 3.3 API Routes

All routes live under `server/app/api/routes/` and are prefixed with `/api` (or `/api/v1` via `settings.API_V1_PREFIX`).

- `health.py`
  - `GET /health`
  - Returns `{"success": true, "data": {"status": "healthy"}}`.
  - Unauthenticated; used for health checks.

- `auth.py` (Sprint 1: Issue #3)
  - `POST /api/auth/register`
    - Validates `RegisterRequest`.
    - Hashes password with `bcrypt`.
    - Inserts user into DB (role from enum).
    - Returns `AuthResponse` + JWT.
  - `POST /api/auth/login`
    - Validates `LoginRequest`.
    - Verifies credentials against stored hash.
    - Returns `AuthResponse` + JWT.
  - `GET /api/auth/me`
    - Uses `get_current_user`.
    - Returns current user profile.

- `courses.py` (Sprint 1: Issue #5)
  - `POST /api/courses`
    - **Professor only** (`require_role("professor")`).
    - Creates new course with auto-generated 6‑character invite code.
  - `GET /api/courses`
    - Returns courses where the user is enrolled or owner.
  - `GET /api/courses/{id}`
    - Returns course detail for enrolled users.
  - `POST /api/courses/join`
    - Student/TA join by invite code.
    - Creates `CourseEnrollment` if not already enrolled.
  - All endpoints use `{ success: true, data: ... }` / `{ success: false, message: ... }` format and enforce role & enrollment rules.

- `sessions.py` (Sprint 1: Issue #7)
  - `POST /api/sessions`
    - Professor only.
    - Creates session for a course; ensures no more than one active session per course.
  - `GET /api/sessions?course_id=X`
    - Returns sessions for the given course (enrolled users).
  - `PUT /api/sessions/{id}`
    - Edit scheduled sessions (professor only).
  - `DELETE /api/sessions/{id}`
    - Delete scheduled sessions only.
  - `PATCH /api/sessions/{id}/status`
    - Transition logic:
      - `scheduled -> active` (fails if another active exists for the same course).
      - `active -> ended` (marks all queued questions as `unresolved`, per `003_add_unresolved_status.sql`).

- `questions.py` (Sprint 1: Issues #8, #9, #10)
  - Student endpoints:
    - `POST /api/questions`
      - Requires `student` role.
      - Validates session is active and student has no other active question in that session.
      - Creates question with initial `queued` status and appropriate priority/category.
    - `GET /api/questions/{id}`
      - Owner student can view their own question.
    - `PUT /api/questions/{id}`
      - Owner can edit only if status is `queued`.
    - `PATCH /api/questions/{id}/withdraw`
      - Sets status to `withdrawn` if current status is `queued` or `in_progress`.
  - TA / professor endpoints:
    - `GET /api/questions?session_id=X`
      - Returns all questions in the session (TA or professor).
      - Sorted by queue logic (priority, submitted_at, deferred behavior).
    - `PATCH /api/questions/{id}/claim`
      - TA only.
      - Sets status to `in_progress`, sets `claimed_by`, `claimed_at`.
      - 400 if already claimed.
    - `PATCH /api/questions/{id}/resolve`
      - TA only.
      - Sets status to `resolved`, writes `resolution_note`.
    - `PATCH /api/questions/{id}/defer`
      - TA only.
      - Sets status to `deferred`, moves question to back of queue based on `deferred_at`.
  - All status changes recalculate queue positions and (in later sprints) will emit real-time events.

### 3.4 Database Migrations (PostgreSQL)

Location: `server/db_migrations/migrations/`

- `001_initial_schema.sql`
  - Initializes core tables and enums, aligning with PRD data models:
    - `users`, `courses`, `course_enrollments`, `sessions`, `questions`, etc.
    - Role, status, category, priority enums.

- `002_core_sprint1_schema.sql`
  - Adds/adjusts schema to fully support Sprint 1 endpoints:
    - Indexes on frequently queried columns (e.g., session_id + status on `questions`).
    - Unique constraints and foreign keys for course enrollment and relationships.
    - Any additional columns needed for queue logic and timestamps.

- `003_add_unresolved_status.sql`
  - Adds the `unresolved` status for questions so that ending a session can mark remaining queued questions accordingly.

---

## 4. Frontend (Client) — Sprint 1 Code Structure

### 4.1 Global Styling and Layout

- `client/src/app/globals.css`
  - Uses Tailwind CSS v4 with `@import "tailwindcss";` and an `@theme` block to define:
    - Colors: background, surface, card, accent, green, amber, red, cyan, purple.
    - Text colors: primary, secondary, muted.
    - Radii: card (14px), input/button (10px), badge (20px).
    - Fonts: DM Sans (sans), JetBrains Mono (mono).
  - These design tokens produce utility classes such as `bg-bg`, `bg-card`, `rounded-card`, etc., used across components.

- `client/src/app/layout.tsx`
  - Root layout component:
    - Imports DM Sans and JetBrains Mono via `next/font/google`.
    - Sets `<html className="dark">` and `<body>` with the font classes.
    - Declares `metadata` for the app (title, description).

### 4.2 Auth Pages (Issue #4)

Located under `client/src/app/(auth)/`:

- `login/page.tsx`
  - Implements the login UI:
    - Email and password inputs with validation feedback.
    - Dark theme card with appropriate radius and accent colors.
    - Submit button with loading state.
    - On submit:
      - Calls backend `/api/auth/login`.
      - On success, stores JWT via `AuthContext` and redirects to `dashboard`.

- `register/page.tsx`
  - Implements registration UI:
    - Name, email, password fields.
    - Role dropdown with options: student, TA, professor.
    - Same dark, card-based design.
    - Calls `/api/auth/register` and then logs user in on success.

### 4.3 Auth Context

- `client/src/context/AuthContext.tsx`
  - Provides global auth state:
    - Current user object (id, email, name, role).
    - JWT access token.
    - Methods: `login`, `logout`, `register`, `refreshUser`.
  - Wraps the app so any page (dashboard, course, session, question form) can access `useAuth()`.

### 4.4 Navigation and Layout Components

- `client/src/components/common/NavBar.tsx`
  - Shared top navigation bar:
    - Back arrow, course/session title where applicable.
    - Session status badge (active/scheduled coloring).
    - Notification bell placeholder with count badge (actual notifications in Sprint 2).
    - User avatar circle with initials (from `AuthContext` user).
  - Used across dashboard, course, and session pages.

### 4.5 Course Dashboard UI (Issue #6)

- `client/src/app/dashboard/page.tsx`
  - Landing page after login:
    - Fetches the user’s courses from `/api/courses`.
    - Displays each as a card with role badge and, for professors, the invite code.
    - Buttons:
      - Professors: “Create Course” (opens modal / inline form).
      - Students/TAs: “Join Course” (invite code input).
    - Empty state when no courses: copy consistent with PRD.

- `client/src/app/courses/[id]/page.tsx`
  - Course detail page:
    - Shows course name, role, and sessions list.
    - Provides access to session view for active/scheduled sessions.

### 4.6 Session View UI (part of Issue #7)

- `client/src/app/sessions/[id]/page.tsx`
  - Session detail page:
    - Shows session title, status badge, and topics.
    - Entry point for:
      - Student: question submission/status (using `QuestionSubmissionForm`).
      - TA: queue view (to be fully realized in Sprint 2 for real-time).
      - Professor: read-only queue plus (in later sprints) analytics.

### 4.7 Student Question Submission Form UI (Issue #9)

- `client/src/components/questions/QuestionSubmissionForm.tsx`
  - Implements the full-question form per PRD:
    - Title (max length), Description, Code Snippet (mono, optional), Error Message (mono, optional), What I’ve Tried.
    - Category dropdown: debugging, conceptual, setup, assignment, other.
    - Priority dropdown: low, medium, high.
    - Character count indicators for long text areas.
    - Full‑width Submit button with loading/disabled states.
  - Behavior:
    - Submits to `/api/questions` for the active session.
    - After successful submission:
      - Shows queue status card:
        - Position, estimated wait time.
        - Question summary.
        - Edit and Withdraw buttons (only when status is `queued`).
      - Claimed state:
        - Green check icon, “Your question is being answered!”, TA name when available.
    - Handles backend errors such as:
      - Submitting to inactive session.
      - Multiple active questions for the same student/session.

### 4.8 Root Page

- `client/src/app/page.tsx`
  - Simple branded entry page that either:
    - Redirects to `dashboard` if already logged in, or
    - Shows a “Get Started” CTA to login/register.
  - Uses dark theme design tokens and layout consistent with NavBar and forms.

---

## 5. How This Relates to SETUP_IMPLEMENTATION_LOG.md

`SETUP_IMPLEMENTATION_LOG.md` is a **chronological log** of setup and environment work. It includes:

- Tooling choices and versions.
- How Next.js and the Python backend were scaffolded.
- Detailed notes on failures (Write tool persistence, passlib vs bcrypt, EmailStr validation) and how they were fixed.
- Final structure verification for server and early client.

This `sprint1.md` builds on that by:

- **Organizing the information by feature and layer** (monorepo, backend, frontend) instead of by time.
- **Including Sprint 1 issue alignment**, so each piece of code is explicitly tied to its GitHub issue.
- **Capturing current backend and frontend files** as they exist now, including:
  - All core API route modules (`auth.py`, `courses.py`, `sessions.py`, `questions.py`, `health.py`).
  - All primary schemas used for Sprint 1 flows.
  - The core UI pages and components involved in auth, dashboard, and question submission.
  - Database migrations up through `003_add_unresolved_status.sql`.

For low-level operational details (exact commands, environment quirks, and historical mistakes), refer to `SETUP_IMPLEMENTATION_LOG.md`. For a **snapshot of Sprint 1’s implemented functionality and structure**, use `sprint1.md`.

---

## 6. Next Steps After Sprint 1

These are beyond Sprint 1 but are referenced by later issues and the PRD:

- Real-time queue updates and notifications (Sprint 2: issues #11–#17).
- TA queue UI with live updates and advanced queue management.
- Similar questions panel and knowledge base search.
- Professor analytics dashboard (trends, categories, TA performance).

Sprint 1 establishes the **foundation**: monorepo, database schema, core auth and course/session/question flows, and the main student-facing form and dashboard. Subsequent sprints will layer real-time behavior, notifications, and analytics on top of this structure.

