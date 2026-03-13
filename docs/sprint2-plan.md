# Sprint 2 Planning Document

**Sprint Duration:** Mar 3 - Mar 13, 2026 (10 days)
**Sprint Goal:** Complete all user-facing features, implement real-time updates, add API documentation, and deploy the application to production.

---

## Sprint Backlog

### User Story 1: Question Submission and Queue
**As a** Student, **I want to** submit a question to an active office hours session **so that** I can get help from a TA.

**Acceptance Criteria:**
- `POST /api/questions` creates a question with title, description, code snippet (optional), error message (optional), what I've tried, category, and priority
- Submission fails if the session is not active (400)
- Submission fails if the student already has an active question (queued or in_progress) in this session (400)
- After submitting, the student sees their queue position and estimated wait time
- Queue position and wait time update in real time via Supabase Realtime
- Students can edit their question while it's in "queued" status
- Students can withdraw their question from the queue

### User Story 2: TA Queue Management
**As a** TA, **I want to** view, claim, resolve, and defer questions **so that** I can efficiently help students during office hours.

**Acceptance Criteria:**
- `GET /api/questions?session_id=X` returns all questions sorted by priority (high first), then by submission time
- TAs see stat cards showing queued, in-progress, and resolved counts
- Clicking a question card expands it to show full details (description, code, error, what was tried)
- `PATCH /api/questions/{id}/claim` sets status to in_progress and records the TA
- `PATCH /api/questions/{id}/resolve` resolves the question with a resolution note (works from both queued and in_progress)
- `PATCH /api/questions/{id}/defer` sends the question to the absolute back of the queue regardless of priority
- All queue changes broadcast in real time to all connected clients
- Claiming an already-claimed question returns 400

### User Story 3: Student Real-Time Queue Experience
**As a** Student, **I want to** see live updates about my question status **so that** I know when a TA is helping me without refreshing the page.

**Acceptance Criteria:**
- When a TA claims the student's question, the UI updates from "waiting" to "being answered" with the TA's name
- When a TA resolves the question, the student is notified
- When a TA defers the question, the student sees their new position in the queue
- Queue position and estimated wait time update automatically on every queue change
- Supabase Realtime subscriptions are scoped to the session channel

### User Story 4: Similar Questions / Knowledge Base
**As a** Student, **I want to** see similar previously-resolved questions while typing my title **so that** I might find my answer without waiting in the queue.

**Acceptance Criteria:**
- `GET /api/knowledge-base/similar?title=X&course_id=Y` returns the top 5 similar resolved questions
- The similar questions panel appears in the submission form when the title is longer than 5 characters
- Each similar question shows the title, resolution note, time resolved, and helpful vote count
- The panel is dismissible
- `GET /api/knowledge-base?course_id=X&search=Y&category=Z` provides paginated search (20 per page) of all resolved questions

### User Story 5: Professor Analytics Dashboard
**As a** Professor, **I want to** view analytics about question patterns and TA performance **so that** I can improve my office hours.

**Acceptance Criteria:**
- Overview tab shows total questions, average wait time, average resolve time, and recent sessions
- Categories tab shows a breakdown of questions by category (debugging, conceptual, setup, assignment, other) with percentages and horizontal progress bars
- Trends tab shows weekly question volume as a bar chart for the last 8 weeks
- TA Performance tab shows each TA's resolved count, average resolve time, and rating
- `GET /api/analytics/export?course_id=X` downloads a CSV file
- All analytics endpoints are Professor-only (403 for other roles)

### User Story 6: Notification System
**As a** user, **I want to** receive notifications about relevant events **so that** I stay informed without constantly checking the app.

**Acceptance Criteria:**
- Students receive notifications when their question is claimed, resolved, or deferred
- TAs receive notifications when a new question is submitted to their session
- All enrolled users are notified when a session becomes active
- Assigned TAs are notified 15 minutes before a session starts
- `GET /api/notifications` returns notifications sorted newest first
- `GET /api/notifications/unread-count` returns the unread count
- `PATCH /api/notifications/{id}/read` and `PATCH /api/notifications/read-all` update read status
- The notification bell in the navbar shows the unread count badge

### User Story 7: API Documentation
**As a** developer or grader, **I want to** view interactive API documentation **so that** I can understand and test every endpoint.

**Acceptance Criteria:**
- FastAPI's built-in `/docs` (Swagger UI) page loads with all 28 endpoints
- Endpoints are grouped by tags: Auth, Courses, Sessions, Questions, Knowledge Base, Analytics, Notifications
- Every endpoint shows summary, description, request/response schemas, and error codes
- Field descriptions appear on all Pydantic model fields
- The "Authorize" button accepts a Bearer JWT token for testing protected endpoints
- `/redoc` page also renders correctly

### User Story 8: Deployment
**As a** user, **I want to** access the application via a public URL **so that** I don't need to run anything locally.

**Acceptance Criteria:**
- Next.js frontend is deployed on Vercel with the `NEXT_PUBLIC_API_URL` environment variable pointing to the backend
- FastAPI backend is deployed on Render with all required environment variables (Supabase URL, key, JWT secret)
- CORS is configured to allow requests from the Vercel frontend URL
- `/docs` and `/redoc` are accessible on the production backend URL
- The full user flow works end-to-end on the deployed version (register, login, submit question, claim, resolve)

---

## Capacity and Assignments

| Team Member | Focus Area |
|---|---|
| Dhruv | Question queue system, API documentation, deployment (Vercel + Render), knowledge base, demo video (first half) |
| Xuan | Professor analytics dashboard, notification system, real-time subscriptions, testing, CI/CD, demo video (second half) |

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Render free tier cold starts (30-60s) | Document in README; consider upgrading to paid tier for grading period |
| Supabase Realtime connection limits on free tier | Scope subscriptions tightly to session channels; unsubscribe on unmount |
| Tight timeline (10 days for all features + deployment) | Prioritize working features over polish; cut scope on analytics CSV export if needed |

---

## Definition of Done
- All endpoints pass manual testing on the deployed version
- Role-based access is enforced on every endpoint
- Real-time updates work for question status changes
- API docs are complete and accessible at `/docs`
- Both frontend and backend are deployed and connected
- Code is committed to the `sprint2` branch
