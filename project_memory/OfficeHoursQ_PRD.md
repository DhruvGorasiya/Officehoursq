# OfficeHoursQ - Product Requirements Document

## Tech Stack

- **Frontend**: Next.js 14+ (TypeScript), Tailwind CSS, Lucide React, Recharts
- **Backend**: FastAPI (Python), Pydantic validation
- **Database**: Supabase (PostgreSQL)
- **Real-time**: Supabase Realtime (Postgres Changes + Broadcast)
- **Auth**: Supabase Auth (email/password, JWT)
- **Structure**: Monorepo: `/client` (Next.js) and `/server` (FastAPI)

## Roles

Three roles: `student`, `ta`, `professor`. Default: deny access. Every endpoint and page checks role.

## Data Models

### User

`id (uuid, pk)`, `email (unique)`, `name`, `role (enum: student|ta|professor)`, `created_at`

### Course

`id (uuid, pk)`, `name`, `invite_code (unique, 6-char alphanum, auto-generated)`, `professor_id (fk -> user)`, `created_at`

### CourseEnrollment

`id (uuid, pk)`, `course_id (fk)`, `user_id (fk)`, `role (enum: student|ta)`, `joined_at`

- Join table. Unique constraint on (course_id, user_id).

### Session

`id (uuid, pk)`, `course_id (fk)`, `title`, `date`, `start_time`, `end_time`, `status (enum: scheduled|active|ended, default: scheduled)`, `topics (text[])`, `is_recurring (bool, default: false)`, `recurring_pattern (enum: weekly|biweekly, nullable)`, `created_by (fk -> user)`, `created_at`

- Constraint: max one `active` session per course_id.

### SessionTaAssignment

`id (uuid, pk)`, `session_id (fk)`, `ta_id (fk -> user)`

### Question

`id (uuid, pk)`, `session_id (fk)`, `course_id (fk)`, `student_id (fk)`, `title (max 200)`, `description (max 2000)`, `code_snippet (nullable, max 5000)`, `error_message (nullable, max 1000)`, `what_tried (max 2000)`, `category (enum: debugging|conceptual|setup|assignment|other)`, `priority (enum: low|medium|high)`, `status (enum: queued|in_progress|resolved|deferred|withdrawn|unresolved, default: queued)`, `claimed_by_ta_id (fk, nullable)`, `resolution_note (nullable, max 2000)`, `helpful_votes (int, default: 0)`, `submitted_at`, `claimed_at (nullable)`, `resolved_at (nullable)`, `deferred_at (nullable)`

- Constraint: one active question (queued or in_progress) per student per session.
- Indexes: (session_id, status), (course_id, status), full-text on (title, description, resolution_note).

### HelpfulVote

`id (uuid, pk)`, `question_id (fk)`, `student_id (fk)`, unique on (question_id, student_id).

### Notification

`id (uuid, pk)`, `user_id (fk)`, `type (enum: question_claimed|question_resolved|question_deferred|question_submitted|session_active|session_starting)`, `message`, `related_question_id (fk, nullable)`, `related_session_id (fk, nullable)`, `is_read (bool, default: false)`, `created_at`

## API Endpoints

All return JSON. Errors: `{ success: false, message: "..." }`. Success: `{ success: true, data: {...} }`.

### Auth

- `POST /api/auth/register` - Public. Body: `{ email, password, name, role }`. Returns JWT + user.
- `POST /api/auth/login` - Public. Body: `{ email, password }`. Returns JWT + user.
- `GET /api/auth/me` - Authenticated. Returns current user.

### Courses

- `POST /api/courses` - Professor only. Body: `{ name }`.
- `GET /api/courses` - Authenticated. Returns user's enrolled/owned courses.
- `GET /api/courses/{id}` - Enrolled users only.
- `POST /api/courses/join` - Student or TA. Body: `{ invite_code }`.

### Sessions

- `POST /api/sessions` - Professor only. Body: `{ course_id, title, date, start_time, end_time, ta_ids[], topics[], is_recurring, recurring_pattern }`.
- `GET /api/sessions?course_id=X` - Enrolled users.
- `PATCH /api/sessions/{id}/status` - Professor only. Body: `{ status }`. Transitions: scheduled->active (if no other active), active->ended (marks remaining queued questions as unresolved).
- `PUT /api/sessions/{id}` - Professor only. Scheduled sessions only.
- `DELETE /api/sessions/{id}` - Professor only. Scheduled sessions only.

### Questions

- `POST /api/questions` - Student only. Body: `{ session_id, title, description, code_snippet, error_message, what_tried, category, priority }`. Fails if session not active or student already has active question.
- `GET /api/questions?session_id=X` - TA or Professor. Returns all questions for session.
- `GET /api/questions/{id}` - Owner student, TA, or Professor.
- `PUT /api/questions/{id}` - Owner student. Only if status is `queued`.
- `PATCH /api/questions/{id}/claim` - TA only. Sets status=in_progress, records claimed_by and claimed_at. Fails if already claimed.
- `PATCH /api/questions/{id}/resolve` - TA only. Body: `{ resolution_note }`. Sets status=resolved. Works from queued or in_progress.
- `PATCH /api/questions/{id}/defer` - TA only. Optional body: `{ note }`. Sets status=deferred then immediately re-queues at back. Clears claimed_by, sets deferred_at=now.
- `PATCH /api/questions/{id}/withdraw` - Owner student. Sets status=withdrawn. Only if queued or in_progress.
- `POST /api/questions/{id}/helpful` - Student only. One vote per student.

### Knowledge Base

- `GET /api/knowledge-base?course_id=X&search=Y&category=Z` - Enrolled users. Searches resolved questions. Paginated (20/page).
- `GET /api/knowledge-base/similar?title=X&course_id=Y` - Student. Returns top 5 similar resolved questions by keyword match.

### Analytics (Professor only)

- `GET /api/analytics/overview?course_id=X` - Total questions, avg wait, avg resolve, recent sessions.
- `GET /api/analytics/categories?course_id=X` - Category breakdown with percentages.
- `GET /api/analytics/trends?course_id=X` - Weekly question volume (last 8 weeks).
- `GET /api/analytics/ta-performance?course_id=X` - Per-TA stats: resolved count, avg time, rating.
- `GET /api/analytics/export?course_id=X` - CSV download.

### Notifications

- `GET /api/notifications` - Authenticated. User's notifications, newest first.
- `GET /api/notifications/unread-count` - Returns `{ count }`.
- `PATCH /api/notifications/{id}/read` - Owner.
- `PATCH /api/notifications/read-all` - Authenticated.

## Real-time (Supabase Realtime)

Clients subscribe to Supabase Realtime channels scoped by session or user.

| Trigger                         | Channel        | Who Receives             | Payload                 |
| ------------------------------- | -------------- | ------------------------ | ----------------------- |
| Question INSERT                 | `session:{id}` | TAs, Professor           | New question object     |
| Question UPDATE (status change) | `session:{id}` | All session participants | Updated question object |
| Notification INSERT             | `user:{id}`    | Target user              | Notification object     |
| Session UPDATE (status)         | `course:{id}`  | All enrolled users       | Updated session object  |

After any question status change, the backend recalculates queue positions and estimated wait times and broadcasts via Supabase Broadcast on the session channel.

## Queue Logic

**Sort order**: Priority (high=0, medium=1, low=2), then `submitted_at` ASC within same priority. Exception: deferred questions go to the absolute back regardless of priority (sorted by `deferred_at`).

**Estimated wait**: `position * avg_resolve_time`. Default 5 min/position if no resolved questions yet. Cap display at "60+ min".

**Recalculate on**: every claim, resolve, defer, withdraw, or new submission.

## UI Layout (Reference: Mockup JSX)

### Design tokens

Dark theme only. BG: `#0A0E17`, Surface: `#111827`, Card: `#161F31`. Accent: indigo `#6366F1`. Green: `#10B981`. Amber: `#F59E0B`. Red: `#EF4444`. Cyan: `#06B6D4`. Purple: `#A855F7`. Font: DM Sans. Mono: JetBrains Mono. Borders: 14px radius on cards, 10px on inputs/buttons, 20px on badges.

### NavBar (all views)

Back arrow | Course name (bold) | Session status badge (green=active, amber=scheduled) | Notification bell (red count badge) | User avatar circle (initials)

### Student View

1. **Submit form** (max-w 520px, centered): Title, Description, Code Snippet (mono, optional), Error Message (mono, optional), What I've Tried, Category + Priority dropdowns side by side, full-width Submit button.
2. **Similar questions panel** (shows when title > 5 chars): Cyan-tinted card above form with matching resolved questions. Dismissible.
3. **Queue status** (after submit, max-w 480px, centered): Clock icon, "You're in the queue!", Position + Est. Wait stat cards, question summary card, Edit + Withdraw buttons.
4. **Claimed state**: Green checkmark, "Your question is being answered!", TA name, green border on card, Edit/Withdraw hidden.

### TA View (max-w 600px)

1. **Stats row**: Queued (indigo) | In Progress (amber) | Resolved (green).
2. **In Progress cards first** (amber border): "In Progress" badge, title, student, tags, expandable. Actions: Resolve, Defer.
3. **Queued cards below** (default border): Category + priority badges, wait time, title, student, expandable. Actions: Claim, Defer, Resolve.
4. **Expanded card**: Description, code block (dark bg, mono), error (red bg, mono), "Tried:" (italic), action buttons.
5. **Empty state**: "No questions in queue. Nice work!"

### Professor View (max-w 640px)

1. **Header**: "Analytics Dashboard" + Export CSV button.
2. **Tabs**: Overview | Categories | Trends | TA Performance.
3. **Overview**: 3 stat cards (Total Questions, Avg Wait, Avg Resolve), recent sessions list.
4. **Categories**: Horizontal progress bars per category with percentages. Colors: Debugging=purple, Setup=cyan, Conceptual=green, Assignment=amber, Other=red. Insight card below.
5. **Trends**: Vertical bar chart (weekly volume, indigo gradient), Peak Week + Peak Session stat cards.
6. **TA Performance**: TA cards with avatar, name, resolved count, avg time, star rating badge.

## Key Decisions

- No "Redirect" action in v1 (underspecified).
- One active question per student per session.
- TAs can resolve without claiming first.
- Deferred questions go to absolute back of queue.
- Professor queue view is read-only.

## Edge Cases

- Submit to inactive session -> 400.
- Second active question in session -> 400.
- Claim already-claimed question -> 400.
- Edit non-queued question -> 400.
- Withdraw resolved question -> 400.
- Activate second session -> 400.
- Delete active session -> 400.
- End session -> all queued questions become `unresolved`, students notified.
- Wrong role -> 403. Missing auth -> 401.

## Notification Triggers

| Type                 | Recipient       | Trigger              |
| -------------------- | --------------- | -------------------- |
| `question_claimed`   | Student (owner) | TA claims question   |
| `question_resolved`  | Student (owner) | TA resolves question |
| `question_deferred`  | Student (owner) | TA defers question   |
| `question_submitted` | Session TAs     | Student submits      |
| `session_active`     | All enrolled    | Session activated    |
| `session_starting`   | Assigned TAs    | 15 min before start  |

## Out of Scope (v1)

Email/push notifications, video/screenshare, OAuth/SSO, file uploads, TA reassignment, dark/light toggle, redirect action, mobile native apps.
