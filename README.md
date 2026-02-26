# OfficeHoursQ

Real-time office hours queue management system for university courses. Three roles: **Student** (submits questions), **TA** (manages the queue), and **Professor** (analytics and session management).

## Tech Stack

| Layer    | Technology                                      |
| -------- | ----------------------------------------------- |
| Frontend | Next.js 14+, TypeScript, Tailwind CSS           |
| Backend  | FastAPI (Python), Pydantic                       |
| Database | PostgreSQL via Supabase                          |
| Auth     | JWT (python-jose) + bcrypt                       |

## Monorepo Structure

```
/
├── client/          # Next.js frontend
│   ├── src/app/     # App Router pages and layouts
│   └── .env.example
├── server/          # FastAPI backend
│   ├── app/
│   │   ├── api/     # Route handlers
│   │   ├── core/    # Config, security, database, dependencies
│   │   ├── models/  # Database models
│   │   ├── schemas/ # Pydantic request/response schemas
│   │   └── services/# Business logic
│   └── .env.example
└── README.md
```

## Prerequisites

- **Node.js** >= 20
- **Python** >= 3.11
- **npm** (comes with Node.js)
- A [Supabase](https://supabase.com) project (free tier works)

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd Officehoursq
```

### 2. Set up environment variables

Copy the example env files and fill in your values:

```bash
cp client/.env.example client/.env.local
cp server/.env.example server/.env
```

You will need your Supabase project URL, anon key, and service role key from the Supabase dashboard under **Settings > API**.

Generate a JWT secret (at least 32 characters):

```bash
openssl rand -hex 32
```

### 3. Start the backend

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000). Interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Start the frontend

In a separate terminal:

```bash
cd client
npm install
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

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
