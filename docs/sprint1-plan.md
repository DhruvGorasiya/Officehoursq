# Sprint 1 Planning Document

**Sprint Duration:** Feb 17 - Mar 2, 2026 (2 weeks)
**Sprint Goal:** Establish project foundation, core backend infrastructure, and authentication system.

---

## Sprint Backlog

### User Story 1: Project Planning and Design
**As a** development team, **we want to** create a comprehensive PRD and interactive mockup **so that** we have a clear blueprint before writing any code.

**Acceptance Criteria:**
- Hand-drawn wireframes exist for all three role-based views (Student, TA, Professor)
- A PRD document covers all data models, API endpoints, role-based access rules, edge cases, and queue logic
- The PRD is written in a format consumable by LLM-assisted tools (concise, explicit, no ambiguity)
- An interactive React mockup exists showing all three views with correct design tokens (colors, fonts, spacing)
- A `.cursorrules` file is created with coding conventions, tech stack details, and references to the PRD and mockup

### User Story 2: Project Scaffolding
**As a** developer, **I want to** set up the monorepo with Next.js frontend and FastAPI backend **so that** both sides of the application can be developed in parallel.

**Acceptance Criteria:**
- Monorepo structure exists with `/client` (Next.js + TypeScript) and `/server` (FastAPI + Python)
- Next.js app initializes with Tailwind CSS v4 and the dark theme design tokens from the mockup
- FastAPI app initializes with Pydantic validation and proper folder structure (`api/routes/`, `schemas/`, `models/`, `core/`, `services/`)
- Supabase client is configured for both database access and authentication
- Environment variables are set up via `.env` files with a `.env.example` template
- Both apps run locally without errors

### User Story 3: Authentication System
**As a** user (Student, TA, or Professor), **I want to** register and log in with email and password **so that** I can access the application with my assigned role.

**Acceptance Criteria:**
- `POST /api/auth/register` creates a new user with email, password, name, and role
- `POST /api/auth/login` returns a JWT token on valid credentials
- `GET /api/auth/me` returns the current user when a valid JWT is provided
- Passwords are hashed (never stored in plain text)
- Invalid credentials return 401
- Duplicate email registration returns 400
- JWT tokens are validated on every protected route via middleware
- Frontend has login and registration pages that call the auth endpoints

### User Story 4: Course Management
**As a** Professor, **I want to** create courses and generate invite codes **so that** students and TAs can join my course.

**Acceptance Criteria:**
- `POST /api/courses` creates a course with an auto-generated 6-character invite code (Professor only)
- `GET /api/courses` returns all courses the user is enrolled in or owns
- `POST /api/courses/join` allows a Student or TA to join a course using an invite code
- Non-professors cannot create courses (403)
- Invalid or expired invite codes return 400
- A user cannot join the same course twice (400)
- `GET /api/courses/{id}` returns course details only for enrolled users

### User Story 5: Session Management
**As a** Professor, **I want to** create and schedule office hours sessions **so that** students know when to come for help.

**Acceptance Criteria:**
- `POST /api/sessions` creates a session with title, date, time, assigned TAs, and topics (Professor only)
- `GET /api/sessions?course_id=X` returns all sessions for a course
- `PATCH /api/sessions/{id}/status` transitions session status (scheduled to active, active to ended)
- Only one session per course can be active at a time (400 if violated)
- `PUT /api/sessions/{id}` updates a scheduled session (cannot edit active or ended sessions)
- `DELETE /api/sessions/{id}` deletes a scheduled session (cannot delete active sessions)
- Ending a session marks all remaining queued questions as "unresolved"

### User Story 6: Database Schema
**As a** developer, **I want to** implement all data models in Supabase **so that** the application has a reliable data layer.

**Acceptance Criteria:**
- All 8 tables exist in Supabase: User, Course, CourseEnrollment, Session, SessionTaAssignment, Question, HelpfulVote, Notification
- Foreign key relationships are correctly defined
- Unique constraints exist on CourseEnrollment(course_id, user_id) and HelpfulVote(question_id, student_id)
- Indexes exist on Question(session_id, status) and Question(course_id, status)
- Full-text search index exists on Question(title, description, resolution_note)
- Enum types are enforced at the database level

---

## Capacity and Assignments

| Team Member | Focus Area |
|---|---|
| Dhruv | PRD, mockup, `.cursorrules`, backend scaffolding, auth system, session management |
| Xuan | Database schema, course management, frontend scaffolding, auth UI pages |

---

## Definition of Done
- All endpoints pass manual testing via Swagger UI or Postman
- Role-based access is enforced on every endpoint
- Code is committed to the `sprint1` branch
- No hardcoded secrets in the codebase
