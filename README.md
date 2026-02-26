# OfficeHoursQ

Real-time office hours queue management for universities. Three roles: **student**, **TA**, and **professor**.

Monorepo layout:

- **`/client`** — Next.js 14+ (TypeScript, Tailwind CSS), dark theme only
- **`/server`** — FastAPI (Python, Pydantic), Supabase (PostgreSQL + auth with JWT)

## Prerequisites

- **Node.js** 18+ and **npm** (for client)
- **Python** 3.11+ and **pip** or **uv** (for server)
- **Supabase** project (for database and auth)

## Quick start

### 1. Environment

Copy the example env files and fill in your values:

```bash
# Client
cp client/.env.example client/.env

# Server
cp server/.env.example server/.env
```

Set `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_JWT_SECRET` in `server/.env`.  
Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (and optionally `NEXT_PUBLIC_API_URL`) in `client/.env`.

### 2. Run the client (Next.js)

```bash
cd client
npm install
npm run dev
```

App: **http://localhost:3000**

### 3. Run the server (FastAPI)

```bash
cd server
pip install -r requirements.txt
# or: uv pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: **http://localhost:8000**  
Docs: **http://localhost:8000/docs**

## Scripts

| Location   | Command        | Description              |
|-----------|----------------|--------------------------|
| `client/` | `npm run dev`  | Start Next.js dev server |
| `client/` | `npm run build`| Build for production     |
| `client/` | `npm run lint` | Run ESLint               |
| `server/` | `uvicorn app.main:app --reload` | Start FastAPI with reload |

## Design tokens (client)

- **Background** `#0A0E17` · **Surface** `#111827` · **Card** `#161F31`
- **Accent** indigo `#6366F1` · **Green** `#10B981` · **Amber** `#F59E0B` · **Red** `#EF4444` · **Cyan** `#06B6D4` · **Purple** `#A855F7`
- **Font** DM Sans · **Mono** JetBrains Mono
- **Radius** cards 14px, inputs/buttons 10px, badges 20px

## License

Private / internal use.
