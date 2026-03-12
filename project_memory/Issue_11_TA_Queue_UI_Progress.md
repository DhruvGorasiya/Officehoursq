# Issue #11 — TA Queue View UI Progress

## 1. Scope of Issue #11

**Goal:** Build the TA queue management view UI for office hour sessions, matching:

- `.cursorrules` and `OfficeHoursQ_PRD.md` student/TA view specs  
- GitHub issue **#11 – Build TA queue view UI** acceptance criteria:
  - Stats row: Queued (indigo), In Progress (amber), Resolved (green)
  - In‑progress cards first with Resolve & Defer
  - Queued cards below with category/priority badges, wait time, Claim/Defer/Resolve
  - Expandable cards showing description, code, error, and “Tried”
  - Empty state: “No questions in queue. Nice work!”
  - Queue sorted by backend priority/position (deferred at back)

This issue is **frontend/UI only** and builds on top of existing Sprint 1 backend endpoints and data models.

---

## 2. Files Touched for Issue #11

- `client/src/app/sessions/[id]/page.tsx`
  - Main **SessionView** page.
  - Contains both **student** view (question submission + status) and **TA/Professor** queue view.

No backend files were changed for this issue; it relies on the existing questions/session APIs and queue logic implemented in Sprint 1.

---

## 3. Current Data Flow (Session + Questions)

- **Auth / role:** Provided by `AuthContext` (from `client/src/context/AuthContext.tsx`).
  - `user.role` distinguishes:
    - `student` → show submission form
    - `ta` / `professor` → show queue view
- **Session and questions fetch:**
  - `GET {API_URL}/sessions/{sessionId}` → `sessionInfo`
  - `GET {API_URL}/questions?session_id={sessionId}` → `questions[]`
  - Both requests include `Authorization: Bearer {token}`.
  - `API_URL` is `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"`.
- **Polling (pre‑realtime):**
  - `SessionView` calls `fetchSessionAndQuestions` on mount and every **10 seconds** via `setInterval`.
  - This is the only “live” behavior right now; there is **no Socket.io / Supabase Realtime** yet.
- **Queue structure from backend:**
  - Each `question` object is expected to include at least:
    - `id`, `title`, `description`, `category`, `priority`, `status`
    - `queue_position` (pre‑sorted by backend queue logic)
    - `student?.name`, `claimer?.name` (optional)
    - `code_snippet`, `error_message`, `what_tried`
  - Frontend **does not** re‑implement priority/deferred sorting; it only:
    - Filters by status (queued/in_progress/deferred/resolved)
    - Uses `queue_position` for display.

---

## 4. TA / Professor Queue View — What’s Implemented

All of the following live in `SessionView` (`client/src/app/sessions/[id]/page.tsx`).

### 4.1 Layout & Role Switch

- `isStaff = user?.role === 'professor' || user?.role === 'ta'`.
- If `!isStaff`: render **student** view with `QuestionSubmissionForm`.
- If `isStaff`: render **TA / Professor queue** view.
- TA/Professor view is now wrapped in:

```tsx
<div className="max-w-[600px] mx-auto">
  {/* stats row + Live Queue */}
</div>
```

This matches the PRD requirement: **max-w-[600px] centered** for TA view.

### 4.2 Stats Row

- Three stat cards built from `questions`:
  - **Queued:** count of questions where `status` is `queued` or `deferred`.
  - **In Progress:** count where `status === 'in_progress'`.
  - **Resolved:** count where `status === 'resolved'`.
- Colors:
  - Queued count uses **indigo/accent** text (`text-accent`).
  - In Progress uses **amber** (`text-amber`).
  - Resolved uses **green** (`text-green`).
- Cards use design tokens: `bg-card`, `border-border`, `rounded-card`, `text-text-*`.

### 4.3 Queue Sections & Ordering

- Derived collections:
  - `allActive`: questions with `status` in `['queued', 'in_progress', 'deferred']` sorted by `queue_position`.
  - `inProgressQueue`: subset where `status === 'in_progress'` (rendered **first**).
  - `waitingQueue`: subset where `status === 'queued' || status === 'deferred'` (rendered **below**).
- **Important:** ordering entirely follows `queue_position` from backend; frontend only filters/splits.

### 4.4 Empty State

- When `allActive.length === 0`, TA view shows:

> “No questions in queue. Nice work!”

…inside a `bg-surface` card with border and icon, matching `.cursorrules`.

### 4.5 In-Progress Cards

- Rendered first, with:
  - **Amber border** (`border-amber`) and subtle amber shadow.
  - POS box showing `queue_position`.
  - Title, “In Progress” badge, student name, category, optional “Claimed by {TA}”.
  - Short clipped description in a dark mono‑style block.
- **Actions:**
  - `Resolve` → `PATCH /questions/{id}/resolve` (with default `resolution_note`).
  - `Defer` → `PATCH /questions/{id}/defer`.
  - Calls reuse existing `handleAction` helper; behavior unchanged from Sprint 1.

### 4.6 Queued / Deferred Cards

- Rendered after in‑progress cards, each with:
  - POS box with `queue_position`.
  - Title + category badge + priority badge:
    - Priority styling:
      - `high` → red tint
      - `medium` → amber tint
      - `low` → indigo/accent tint
  - Deferred questions show a purple “Deferred” badge.
  - Student name + **approximate wait time**: `~{queue_position * 5} min`.
  - Short clipped description in dark mono‑style block.
- **Actions:**
  - `Claim` → `PATCH /questions/{id}/claim`.
  - `Resolve` → `PATCH /questions/{id}/resolve`.
  - `Defer` → `PATCH /questions/{id}/defer`.
  - All wired through the same `handleAction` function as before.

---

## 5. New Work Done in Issue #11 (Key Additions)

### 5.1 Centered TA Queue Layout

- TA/Professor section is constrained to `max-w-[600px] mx-auto`, aligning with:
  - `.cursorrules` **TA View (max-w-[600px] centered)**.
  - Student card layout width for consistency.

### 5.2 Expandable Question Cards

- New local state in `SessionView`:

```tsx
const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null);
```

- Both **in‑progress** and **queued/deferred** cards get a “View details / Hide details” toggle:
  - Button with `ChevronDown` icon that rotates when expanded.
  - Only **one** question is expanded at a time (single‑expand behavior).

#### Expanded Details Content

When a card is expanded, the following appear under a top border:

- **Description**  
  - Full text shown with `whitespace-pre-wrap` to preserve user formatting.
- **Code Snippet** (if `code_snippet` present)  
  - Rendered in a dark mono block:
    - `bg-[#0D1117]`, `font-mono`, `text-xs`, `border-border`, `whitespace-pre-wrap`, `overflow-x-auto`.
- **Error Message** (if `error_message` present)  
  - Rendered in a red‑tinted mono block:
    - `bg-red/10`, `text-red`, `border border-red/30`, `font-mono`, `overflow-x-auto`.
- **“Tried” Section** (if `what_tried` present)  
  - Label “Tried” is italic and uses `text-text-secondary`.
  - Content uses `whitespace-pre-wrap` to keep step formatting readable.

The summary header content (POS, title, badges, short description) remains unchanged, so the list is still scannable at a glance.

---

## 6. What’s NOT Done Yet (For Issue #12 and Beyond)

These items are intentionally out of scope for issue #11 and should be addressed by **issue #12 (real-time updates)** and later issues:

1. **True real-time updates**
   - Currently, the queue view relies on **polling every 10 seconds**.
   - There is **no Socket.io / Supabase Realtime** subscription yet.
   - Issue #12 should:
     - Replace or augment polling with real-time events for:
       - New question submitted
       - Question claimed/resolved/deferred/withdrawn
       - Queue position changes
     - Subscribe to per‑session channels (e.g., `session:{sessionId}`) as defined in `.cursorrules`.

2. **Frontend handling of real-time events**
   - `SessionView` currently re-fetches the full question list on every update.
   - For issue #12, consider:
     - Either incremental updates from real-time events, or
     - Triggering `fetchSessionAndQuestions` when a real-time event is received.

3. **Advanced queue metrics in the TA view**
   - Current stats row is purely counts.
   - Any future enhancements (e.g., average wait time, average resolve time) should be defined and implemented under issue #12 or the queue logic issue (#17), not here.

4. **Backend changes**
   - No backend logic was modified for this issue.
   - Any changes to:
     - Queue sorting rules,
     - Question payload shape,
     - Real-time event payloads
   - …should be tracked and documented under their respective backend issues (especially #12 and #17).

---

## 7. Guidance for Issue #12 (How to Build on This)

When starting **issue #12 – real-time updates**, you can rely on the following guarantees from issue #11:

- `SessionView` already:
  - Knows the `sessionId` and `user` role.
  - Has a single place (`fetchSessionAndQuestions`) to refresh all queue data.
  - Splits TA view into in‑progress vs queued/deferred using status and `queue_position`.
  - Presents the full TA experience (layout, cards, actions) without additional UI changes.

**Recommended direction for issue #12:**

1. **Wire real-time client in the frontend:**
   - Add a real-time hook or context (e.g., `useSocket` / `useRealtime`) that:
     - Connects on login with JWT.
     - Joins `session:{sessionId}` room when `SessionView` mounts.
     - Listens for question/session events.

2. **Trigger refresh on events:**
   - On relevant events (question added/updated, queue updated), call `fetchSessionAndQuestions()` instead of waiting for the 10s poll.
   - Optionally, remove or reduce the polling interval once real-time is stable.

3. **Keep TA UI stable:**
   - Do **not** change the TA layout or card structure unless the PRD is updated.
   - Focus on injecting fresher data into the existing view, not redesigning it.

By treating this file as the **handoff document** for issue #12, we ensure that real-time work can focus entirely on connectivity and data freshness, while preserving the TA queue UX and acceptance criteria implemented in issue #11.

