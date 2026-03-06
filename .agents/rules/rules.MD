---
trigger: always_on
---

# OfficeHoursQ - Cursor Rules
# Real-time office hours queue management app with three user roles.


## Project Overview

OfficeHoursQ is a real-time queue management tool for university office hours. Three roles: Student (submits questions), TA (manages the queue), Professor (analytics and session management). Students submit structured questions during active sessions. TAs claim, resolve, or defer them. Professors view analytics and control sessions.


## Tech Stack

- Frontend: Next.js 14+ (TypeScript), Tailwind CSS, Lucide React icons, Recharts
- Backend: FastAPI (Python), Pydantic for validation
- Database: Supabase (PostgreSQL)
- Real-time: Supabase Realtime (Postgres Changes + Broadcast)
- Auth: Supabase Auth (email/password, JWT)
- Monorepo: `/client` (Next.js) and `/server` (FastAPI)
- No state management libraries. Use React Context for auth and socket state. useState/useEffect for everything else.


## Monorepo Structure

```
/
├── client/src/
│   ├── components/         # Grouped by feature: auth/, common/, student/, ta/, professor/, course/, session/, notifications/
│   ├── pages/              # Next.js pages (or app/ for App Router)
│   ├── hooks/              # useAuth, useQueue, useRealtime, etc.
│   ├── context/            # AuthContext, RealtimeContext
│   ├── services/           # API call wrappers (fetch/axios)
│   └── utils/
├── server/
│   ├── models/             # Pydantic schemas (PascalCase)
│   ├── routers/            # FastAPI routers (snake_case files)
│   ├── controllers/        # Business logic (snake_case)
│   ├── middleware/         # auth.py (JWT verify), role_check.py
│   ├── utils/              # queue_calculator.py, etc.
│   ├── config/             # database.py, supabase.py
│   └── main.py             # FastAPI entry point
└── .cursorrules
```


## Source of Truth (priority order)

1. `OfficeHoursQ_PRD.md` — Behavioral truth: data models, API specs, validation, edge cases, queue logic. PRD wins over mockup on behavior.
2. `OfficeHoursQ-Mockup.jsx` — Visual truth: colors, layout, component styles, interaction flows. Mockup wins over wireframes on layout.
3. `OfficeHoursQ_Implementation_Plan.md` — Build order truth. Follow phases exactly.
4. Hand-drawn wireframes — Secondary visual reference only.


## Data Models (Quick Reference)

All models are PostgreSQL tables managed via Supabase. See PRD for full field definitions and constraints.

- **User**: id (uuid pk), email (unique), name, role (enum: student|ta|professor), created_at
- **Course**: id, name, invite_code (6-char unique auto-generated), professor_id (fk→user), created_at
- **CourseEnrollment**: id, course_id (fk), user_id (fk), role (enum: student|ta), joined_at. Unique on (course_id, user_id).
- **Session**: id, course_id, title, date, start_time, end_time, status (enum: scheduled|active|ended), topics (text[]), is_recurring, recurring_pattern (enum: weekly|biweekly nullable), created_by (fk→user). Constraint: max one active session per course.
- **SessionTaAssignment**: id, session_id (fk), ta_id (fk→user)
- **Question**: id, session_id, course_id, student_id, title (max 200), description (max 2000), code_snippet (nullable, max 5000), error_message (nullable, max 1000), what_tried (max 2000), category (enum: debugging|conceptual|setup|assignment|other), priority (enum: low|medium|high), status (enum: queued|in_progress|resolved|deferred|withdrawn|unresolved), claimed_by_ta_id (nullable fk), resolution_note (nullable), helpful_votes (int default 0), submitted_at, claimed_at, resolved_at, deferred_at. Constraint: one active question (queued or in_progress) per student per session. Indexes: (session_id, status), (course_id, status), full-text on (title, description, resolution_note).
- **HelpfulVote**: id, question_id (fk), student_id (fk). Unique on (question_id, student_id).
- **Notification**: id, user_id (fk), type (enum: question_claimed|question_resolved|question_deferred|question_submitted|session_active|session_starting), message, related_question_id (nullable fk), related_session_id (nullable fk), is_read (bool default false), created_at


## Queue Logic

- Sort: priority (high=0, medium=1, low=2), then submitted_at ASC within same priority.
- Exception: deferred questions always go to the absolute back, sorted by deferred_at.
- Estimated wait: position × avg_resolve_time. Default 5 min/position if no history. Cap display at "60+ min".
- Recalculate on: every claim, resolve, defer, withdraw, or new submission. Broadcast updated positions via Supabase Broadcast on the session channel.


## Role-Based Access (Default: Deny)

- **Student**: submit/edit/withdraw own questions, vote helpful, view own queue status, search knowledge base, view similar questions
- **TA**: view queue, claim/resolve/defer questions, view question details
- **Professor**: create/manage courses and sessions, activate/end sessions, view analytics, export CSV. Queue view is read-only.
- Wrong role → 403. Missing/invalid auth → 401.


## API Conventions

- All routes under `/api`. Naming: `/api/plural-noun`.
- Success: `{ success: true, data: {...} }` — Error: `{ success: false, message: "..." }`
- Every endpoint: try/except, no raw stack traces, Supabase JWT verification middleware, role check as second layer, Pydantic validation on all request bodies.


## Real-time (Supabase Realtime)

Clients subscribe to Supabase Realtime channels scoped by session or user.

| Trigger | Channel | Recipients | Payload |
|---|---|---|---|
| Question INSERT | `session:{id}` | TAs, Professor | New question object |
| Question UPDATE (status) | `session:{id}` | All session participants | Updated question object |
| Notification INSERT | `user:{id}` | Target user | Notification object |
| Session UPDATE (status) | `course:{id}` | All enrolled users | Updated session object |

After any question status change, recalculate queue positions and estimated wait times, then broadcast via Supabase Broadcast on the session channel. Never rely on polling.


## Design Tokens

Dark theme only. Define in Tailwind config.

| Token | Value |
|---|---|
| BG | #0A0E17 |
| Surface | #111827 |
| Card | #161F31 |
| Border | #1E293B |
| Accent (indigo) | #6366F1 |
| Green | #10B981 |
| Amber | #F59E0B |
| Red | #EF4444 |
| Cyan | #06B6D4 |
| Purple | #A855F7 |
| Text primary | #F1F5F9 |
| Text secondary | #94A3B8 |
| Text muted | #64748B |
| Font | DM Sans |
| Mono | JetBrains Mono |
| Radius | 14px cards, 10px inputs/buttons, 20px badges |


## UI Layout Summary

**NavBar (all views):** Back arrow, course name, session status badge (green=active, amber=scheduled), notification bell with red count badge, user avatar with initials.

**Student View (max-w-[520px]):** Submit form (Title, Description, Code Snippet mono optional, Error Message mono optional, What I've Tried, Category + Priority dropdowns side-by-side, full-width Submit). Similar questions panel appears when title > 5 chars (cyan-tinted, dismissible). After submit (max-w-[480px]): position + wait stat cards, question summary, Edit + Withdraw buttons. Claimed state: green checkmark, TA name, green border, Edit/Withdraw hidden.

**TA View (max-w-[600px]):** Stats row (Queued indigo, In Progress amber, Resolved green). In-Progress cards first (amber border). Queued cards below (default border). Expanded card: description, code block (mono, dark bg), error (red bg mono), "Tried:" italic, action buttons. Queued actions: Claim, Defer, Resolve. In-progress actions: Resolve, Defer. No Redirect button (v1). Empty state: "No questions in queue. Nice work!"

**Professor View (max-w-[640px]):** "Analytics Dashboard" header + Export CSV. Tabs: Overview, Categories, Trends, TA Performance. Overview: 3 stat cards + recent sessions. Categories: horizontal progress bars (Debugging=purple, Setup=cyan, Conceptual=green, Assignment=amber, Other=red) + insight card. Trends: vertical bar chart (indigo gradient) + Peak Week/Session stat cards. TA Performance: avatar, name, resolved count, avg time, star rating.


## Naming Conventions

- React components: PascalCase. Hooks: usePrefix. Python files: snake_case. Pydantic models: PascalCase.
- DB tables: lowercase snake_case plural (e.g., course_enrollments). CSS: Tailwind only.
- Env vars: UPPER_SNAKE_CASE (SUPABASE_URL, SUPABASE_SERVICE_KEY, JWT_SECRET).


## Git / Workflow

- Branches: `feature/{N}-description`, `fix/{N}-description`, `chore/{N}-description`
- Commits: `type(scope): description [#N]` — types: feat, fix, refactor, chore, docs, test, style. Under 72 chars. Commit per meaningful unit.
- PRs: one per issue, linked issue, squash merge, requires review + passing tests.


## Testing

- Backend: pytest + httpx for API integration tests.
- Frontend: Vitest + React Testing Library.
- 70% minimum coverage on controllers and utils.
- Every endpoint: at least one happy-path and one error-path test.
- Feature is not complete until manually tested in browser and automated tests pass.


## Do's

- Validate on both frontend (UX) and backend with Pydantic (security).
- Handle loading, success, and error states for every async call.
- Broadcast Supabase Realtime events for any state change visible to other users.
- Check role permissions before implementing any endpoint or page.
- Use Tailwind custom theme to define design tokens.
- Use environment variables for all secrets. Never hardcode.
- Add PostgreSQL indexes on (session_id, status) and (course_id, status) on questions table.


## Don'ts

- No inline styles, CSS modules, or styled-components — Tailwind only.
- No Redux, Zustand, or other state libraries.
- No "Redirect" action on TA view (out of scope v1).
- No email/push notifications, video, OAuth/SSO, file uploads, dark/light toggle, or mobile native (all out of scope v1).
- No raw error stack traces to client.
- No plain-text passwords — Supabase Auth handles hashing.
- No secrets in code — use .env.


## Edge Cases (Always Handle)

- Submit to inactive session → 400
- Student already has active question in session → 400
- Claim already-claimed question → 400
- Edit non-queued question → 400
- Withdraw resolved question → 400
- Activate second session for same course → 400
- Delete active session → 400
- End session → all queued questions become `unresolved`, notify affected students
- Wrong role → 403 | Missing/invalid JWT → 401


## Security Checklist

- Supabase Auth handles password hashing. Never store raw passwords.
- Verify Supabase JWT on every protected endpoint using the Supabase service key.
- Pydantic validation on all input. Check object ownership before edits/deletes.
- Rate-limit auth endpoints. CORS restricted in production.
- Never log passwords, full JWTs, or Supabase service keys.
- Use Row Level Security (RLS) in Supabase as a second layer of access control.

## Github Issues
Sprint 1
#1 Set up project monorepo and dev environment (chore, high)
#2 Set up Supabase database schema and migrations (backend, chore, high)
#3 Implement auth endpoints (register, login, me) (backend, feature, high)
#4 Build auth UI (register, login pages) (frontend, feature, high)
#5 Implement course CRUD and join endpoints (backend, feature, high)
#6 Build course dashboard UI (frontend, feature, high)
#7 Implement session CRUD and status management endpoints (backend, feature, high)
#8 Implement question submission and retrieval endpoints (backend, feature, high)
#9 Build student question submission form UI (frontend, feature, high)
#10 Implement TA queue actions (claim, resolve, defer) (backend, feature, high)
Sprint 2
#11 Build TA queue view UI (frontend, feature, high)
#12 Implement real-time updates with Supabase Realtime (fullstack, feature, high)
#13 Implement knowledge base search endpoints (backend, feature, medium)
#14 Build similar questions panel and knowledge base UI
#15 Build professor analytics dashboard
#16 Implement notification system
#17 Implement queue logic (priority sorting and estimated wait) (backend, feature, medium)