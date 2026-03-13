# Sprint 1 Retrospective

**Sprint Duration:** Feb 17 - Mar 2, 2026
**Sprint Goal:** Establish project foundation, core backend infrastructure, and authentication system.
**Sprint Outcome:** Goal met. All planned user stories completed.

---

## What Went Well

**AI-assisted planning saved significant time.** Using Claude's web interface to go from hand-drawn wireframes to a full PRD and interactive React mockup compressed what would normally be a week of planning into a few hours. The PRD was specifically written to be LLM-consumable, which paid off immediately when using Cursor for implementation.

**The `.cursorrules` file measurably improved code quality.** We ran a comparison (documented in HW3) where Cursor scaffolded the same project with and without the rules file. The with-rules run produced Pydantic validation, role-based middleware, correct API response envelopes, and caught real bugs (like the passlib/bcrypt incompatibility). The without-rules run left broken dependencies undetected and used a flatter, less organized project structure.

**Supabase simplified the stack.** Choosing Supabase gave us the database, authentication, and real-time infrastructure in one platform. We originally considered Weaviate for the knowledge base feature, but realized the similar-questions search is standard keyword matching, not vector similarity. Dropping Weaviate eliminated an unnecessary dependency.

**FastAPI's built-in features accelerated backend work.** Pydantic models gave us input validation for free, and the auto-generated OpenAPI docs meant we could test endpoints immediately via Swagger UI without any extra setup.

---

## What Didn't Go Well

**Tech stack mismatch between documents.** The initial system prompt (`.cursorrules`) referenced Express, MongoDB, and Socket.io, but the PRD specified FastAPI, Supabase, and Supabase Realtime. This caused confusion early on when Cursor generated code that didn't match the intended stack. We had to update the `.cursorrules` file to align with the PRD.

**Underestimated Tailwind v4 migration effort.** Tailwind v4 uses a CSS-based configuration (`@theme`) instead of the traditional `tailwind.config.ts`. Some components initially didn't render correctly because we used v3 syntax. This took extra debugging time.

**Database schema iteration.** The initial schema didn't account for all the edge cases in the PRD (like the one-active-question-per-student-per-session constraint). We had to revise the schema twice before it matched the PRD completely.

---

## What We'd Change

**Align all project documents before coding starts.** The system prompt, PRD, and implementation plan should all reference the same tech stack from day one. Having conflicting documents wastes time and confuses AI tools.

**Invest more time in Supabase Row Level Security (RLS) policies early.** We implemented role-based access in the FastAPI middleware, but setting up RLS policies at the database level as well would add a second layer of security.

**Set up CI/CD from the first sprint.** We deferred pipeline setup to Sprint 2, but having automated linting and tests running from the start would have caught issues earlier.

---

## Sprint Velocity

| Metric | Value |
|---|---|
| Stories planned | 6 |
| Stories completed | 6 |
| Bugs discovered | 3 (passlib/bcrypt compat, Tailwind v4 config, schema constraints) |
| Bugs fixed | 3 |
