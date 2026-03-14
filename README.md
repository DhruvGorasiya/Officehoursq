## OfficeHoursQ

Real-time office hours queue management system for university courses. Three roles: **Student** (submits questions), **TA** (manages the queue), and **Professor** (analytics and session management).

### Demo Video Link

https://youtu.be/nLZI8-vQQw4

### Linkedin Blog Post

https://www.linkedin.com/posts/dhruvgorasiya_we-sat-in-office-hours-for-40-minutes-la[…]m=member_desktop&rcm=ACoAADlU_pAB-97_I52bpF29lLa7M4LWPtTqG6A

### Tech Stack

| Layer        | Technology                                                                 |
| ----------- | -------------------------------------------------------------------------- |
| Frontend    | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS                |
| Backend     | FastAPI (Python), Pydantic, `pydantic-settings`                            |
| Database    | PostgreSQL via Supabase (SQL migrations in `server/db_migrations`)         |
| Realtime    | Supabase Realtime broadcast channels (`session:{id}`, `user:{id}`, etc.)   |
| Auth        | Supabase Auth (JWT), validated server-side with `supabase.auth.get_user`   |

Development was carried out using two AI-assisted modalities: **[Cursor](https://cursor.com)** and **[Claude.ai](https://claude.ai)**.

### Monorepo Structure

```text
/
├── client/                  # Next.js frontend
│   ├── src/app/             # App Router pages and layouts
│   ├── src/components/      # Feature-oriented React components
│   ├── src/context/         # Auth context and providers
│   ├── src/hooks/           # Realtime and other custom hooks
│   ├── src/lib/             # API helpers, Supabase client
│   └── .env.example
├── server/                  # FastAPI backend
│   ├── app/
│   │   ├── api/routes/      # Route handlers (auth, courses, sessions, questions, etc.)
│   │   ├── core/            # Config, database client, dependencies
│   │   ├── schemas/         # Pydantic request/response schemas & enums
│   │   ├── utils/           # Queue metrics, realtime helpers
│   │   └── main.py          # FastAPI app setup and router registration
│   ├── db_migrations/       # SQL schema migrations and seed data
│   └── .env.example
└── README.md
```

---

## Features

- **Students**
  - Submit structured questions to an active session with title, description, code snippet, error message, what they tried, category, and priority.
  - See their position in the queue and an estimated wait time that updates in real time.
  - Edit or withdraw their own queued questions; vote resolved questions as helpful.
  - View a knowledge base of resolved questions per course and see similar questions while typing.

- **TAs**
  - View the full queue for a session with live updates (queued, in-progress, deferred, resolved).
  - Claim questions, resolve them (with resolution note), or defer them (send to the back of the queue).
  - See queue ordering by priority then submission time, with deferred questions always at the end.

- **Professors**
  - Create and manage courses and sessions; assign TAs to sessions.
  - Activate/End sessions (enforcing at most one active session per course).
  - View analytics dashboards: overview stats, category breakdown, trends, and TA performance.
  - Export analytics data as CSV.

---

## Backend Overview (FastAPI + Supabase)

The backend lives in `server/app` and exposes a versioned API under `/api/v1`.

- **Auth (`app/api/routes/auth.py`)**
  - Uses Supabase Auth for sign-up and login.
  - On registration, creates a profile row in the `users` table with role metadata.
  - On login, returns a Supabase JWT access token and the user profile; the frontend sends this token as `Authorization: Bearer <token>` on all subsequent requests.
  - `GET /auth/me` validates the token via `supabase.auth.get_user` and returns the current user.

- **Courses & Enrollments**
  - Professors can create courses; students and TAs join via invite codes.
  - Enrollment is stored in a `course_enrollments` table and checked on protected endpoints.

- **Sessions (`app/api/routes/sessions.py`)**
  - Professors create sessions for a course with scheduled time windows and optional TA assignments.
  - Only the course professor can edit or delete scheduled sessions.
  - Status transitions:
    - `scheduled → active`: only allowed if there is no other active session for the course.
    - `active → ended`: marks all remaining queued/in-progress/deferred questions as `unresolved` with a standard resolution note.
  - Broadcasts session status changes via Supabase Realtime (`course:{course_id}` and `session:{session_id}`).

- **Questions & Queue (`app/api/routes/questions.py`)**
  - Students can submit one active question (queued or in-progress) per session.
  - Queue ordering:
    - Primary: priority (`high` before `medium` before `low`).
    - Secondary: submission time (earlier first).
    - Deferred questions are always moved to the very back of the queue and ordered by `deferred_at`.
  - Estimated wait time:
    - Uses historical resolved questions in the session to compute average resolution time.
    - Each question’s estimated wait is \( position \times \text{avg\_resolve\_time} \), capped at 60 minutes.
  - Core actions:
    - **Submit** (student): adds a queued question and triggers queue recalculation.
    - **Claim** (TA/professor): moves a question to in-progress and records `claimed_by`.
    - **Resolve** (TA/professor): marks a question resolved, sets `resolved_at` and resolution note.
    - **Defer** (TA/professor): marks deferred, clears claim info, and sends it to the back of the queue.
    - **Withdraw** (student): withdraws their own active question.
    - **Helpful vote** (student): records helpful votes on resolved questions.
  - Every state change recalculates queue positions and broadcasts `queue:updated` and specific events (`question:submitted`, `question:claimed`, etc.) over Supabase Realtime.

- **Knowledge Base (`app/api/routes/knowledge_base.py`)**
  - Authenticated and enrolled users can search resolved questions by course.
  - Full-text–like search using `ILIKE` across title, description, and resolution notes.
  - Uses a Supabase Postgres RPC function `find_similar_questions` to power similar-question suggestions.

- **Analytics (`app/api/routes/analytics.py`)**
  - Provides endpoints for overview stats, category distributions, trends, and TA performance per course.
  - Supports CSV export for offline analysis.

---

## Frontend Overview (Next.js App Router)

The frontend lives in `client/` and uses the Next.js App Router.

- **Routing**
  - `/(auth)/login`, `/(auth)/register`: authentication flows.
  - `/courses/[courseId]`: course dashboard, session listing, and navigation for each role.
  - `/sessions/[sessionId]`: live queue view for students, TAs, and professors.
  - `/courses/[courseId]/analytics`: professor analytics dashboard (tabs: Overview, Categories, Trends, TA Performance).
  - `/courses/[courseId]/knowledge-base`: course-specific knowledge base search and browsing.

- **Auth Context**
  - `AuthContext` stores the current user and JWT token in React state and `localStorage`.
  - On load, it restores the token from storage and validates it via `/auth/me`; on failure, it clears state and forces re-authentication.
  - Provides helpers for login, logout, and checking role on the client.

- **Realtime Updates**
  - A shared `useRealtimeChannel` hook subscribes to Supabase Realtime channels:
    - `session:{sessionId}` for queue updates and question events.
    - `course:{courseId}` for session status changes.
    - `user:{userId}` for notifications.
  - Components update UI in real time when broadcast events arrive (queue reordering, status changes, notifications).

- **Knowledge Base & Analytics**
  - `lib/knowledgeBaseApi.ts` and `lib/analyticsApi.ts` wrap backend endpoints with typed fetch helpers.
  - Charts and visualizations use Recharts; icons use `lucide-react`.

---

## Database & Migrations

- PostgreSQL schema managed via SQL migrations under `server/db_migrations/migrations/`.
- Core tables include:
  - `users`, `courses`, `course_enrollments`
  - `sessions`, `session_ta_assignments`
  - `questions`, `helpful_votes`
- Additional migrations add:
  - `unresolved` status and queue metadata (`queue_position`, `estimated_wait_minutes`).
  - RPCs and indexes used for knowledge base search, including the `find_similar_questions` function.
- A large seed script (`seed_cs5432_ai_assisted_coding.sql`) provides demo data for development.

To apply migrations and seeds, run the SQL files inside your Supabase project using the SQL editor or a migration workflow of your choice.

---

## Local Development

### Prerequisites

- **Node.js** >= 20
- **Python** >= 3.11
- **npm** (comes with Node.js)
- A [Supabase](https://supabase.com) project (free tier is sufficient)

### 1. Clone the repository

```bash
git clone <repo-url>
cd Officehoursq
```

### 2. Configure environment variables

Copy the example env files and fill in your values:

```bash
cp client/.env.example client/.env.local
cp server/.env.example server/.env
```

At minimum you will need:

- Supabase project URL
- Supabase anon key (frontend)
- Supabase service role key (backend)
- A strong JWT secret used by the backend for additional signing/verification if configured

Refer to your Supabase dashboard under **Settings → API** to obtain the keys.

### 3. Start the backend

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### 4. Start the frontend

In a separate terminal:

```bash
cd client
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## Deployed Backend & API Docs

The backend is deployed at **https://officehoursq.onrender.com**. You can use the following URLs to explore and test the API:

| URL | Description |
|-----|-------------|
| [**https://officehoursq.onrender.com/docs**](https://officehoursq.onrender.com/docs) | **Swagger UI** – interactive API documentation; try endpoints and authorize with a JWT. |
| [**https://officehoursq.onrender.com/redoc**](https://officehoursq.onrender.com/redoc) | **ReDoc** – alternative API documentation view. |
| **https://officehoursq.onrender.com/api/v1/openapi.json** | OpenAPI 3 schema (JSON). |

The API base URL for the deployed backend is `https://officehoursq.onrender.com/api/v1`. On the free tier, the service may take 30–60 seconds to wake up on the first request.

---

## Design Tokens

The app uses a dark-only theme. Key tokens configured in Tailwind:

| Token            | Value     | Usage                   |
| ---------------- | --------- | ----------------------- |
| `bg`             | `#0A0E17` | Page background         |
| `surface`        | `#111827` | Surface/section bg      |
| `card`           | `#161F31` | Card backgrounds        |
| `border`         | `#1E293B` | Border color            |
| `accent`         | `#6366F1` | Primary accent (indigo) |
| `green`          | `#10B981` | Success states          |
| `amber`          | `#F59E0B` | Warning / in-progress   |
| `red`            | `#EF4444` | Error / destructive     |
| `cyan`           | `#06B6D4` | Info / setup            |
| `purple`         | `#A855F7` | Debugging category      |
| `text-primary`   | `#F1F5F9` | Primary text            |
| `text-secondary` | `#94A3B8` | Secondary text          |
| `text-muted`     | `#64748B` | Muted text              |

**Fonts:** DM Sans (body), JetBrains Mono (code)  
**Border Radius:** 14px cards, 10px inputs/buttons, 20px badges
