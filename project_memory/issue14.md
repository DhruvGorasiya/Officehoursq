## Issue #14 – Similar Questions Panel & Knowledge Base UI

### 1. Scope and Behavior

- Implemented the **student similar-questions suggestion panel**, the **course knowledge base browse/search page**, **helpful-vote mechanics**, and **navigation hooks** so everything is reachable via UI (no manual URLs).
- All behavior follows the PRD and the Issue #14 acceptance criteria:
  - Similar questions panel appears while typing a question title (title length \> 5).
  - Knowledge base page allows search, category filter, pagination, and helpful voting.
  - Helpful voting is one vote per student per question.

---

### 2. Backend Changes – Helpful Vote Endpoint

**File:** `server/app/api/routes/questions.py`

- **New route:** `POST /api/v1/questions/{q_id}/helpful`

Implementation (high level):

- Signature:
  - `@router.post("/{q_id}/helpful")`
  - `mark_question_helpful(q_id: str, user: dict = Depends(require_role("student")))`
  - Only authenticated **students** can hit this endpoint (via `require_role("student")`).

- **Flow:**
  1. Extract `student_id` from `user["sub"]`.
  2. Fetch the question:
     - `supabase.table("questions").select("id, status, course_id, helpful_votes").eq("id", q_id).single().execute()`
  3. Validate:
     - If not found: `404` – `{ success: false, message: "Question not found" }`.
     - If `status != "resolved"`: `400` – `{ success: false, message: "Only resolved questions can be marked helpful" }`.
  4. Insert into `helpful_votes`:
     - `supabase.table("helpful_votes").insert({ "question_id": q_res.data["id"], "student_id": student_id }).execute()`
     - Wrapped in `try/except`:
       - On any insert error, assume unique-constraint collision (`(question_id, student_id)`):
         - Return `400` – `{ success: false, message: "Already voted helpful" }`.
  5. Increment the denormalized counter:
     - Compute `new_count = (q_res.data.get("helpful_votes") or 0) + 1`.
     - `update_res = supabase.table("questions").update({ "helpful_votes": new_count }).eq("id", q_id).execute()`
  6. Response:
     - If `update_res.data` present, return that row:
       - `{ success: true, data: updated_question }`
     - Else, fallback to `{ success: true, data: { "id": q_id, "helpful_votes": new_count } }`.
  7. Any unexpected exception:
     - `400` – `{ success: false, message: str(e) }`.

**Data model recap (from migration `004_knowledge_base_search.sql`):**

- `questions` table:
  - `course_id UUID NOT NULL`
  - `helpful_votes INTEGER NOT NULL DEFAULT 0`
  - `search_vector tsvector` (generated from `title`, `description`, `resolution_note`).
- `helpful_votes` table:
  - `id UUID PRIMARY KEY`
  - `question_id UUID REFERENCES public.questions(id) ON DELETE CASCADE`
  - `student_id UUID REFERENCES public.users(id) ON DELETE CASCADE`
  - `created_at TIMESTAMPTZ DEFAULT now()`
  - `UNIQUE (question_id, student_id)` to enforce one vote per student per question.

---

### 2.1 Backend: Knowledge Base Search (GET /api/v1/knowledge-base)

**File:** `server/app/api/routes/knowledge_base.py`

- **Route:** `GET ""` (mounted under `/api/v1/knowledge-base`).
- **Query params:** `course_id` (required), `search` (optional), `category` (optional), `page` (default 1).
- **Auth:** `get_current_user`; enrollment checked via `check_enrollment` (professor must own course, others must be in `course_enrollments`). Non-enrolled get `403`.

**Current behavior:**

- Base query: `questions` with `status = "resolved"`, `course_id = course_id`, select fields including `student:users!questions_student_id_fkey(name)`.
- **When `search` is present (non-empty after strip):**
  - Search uses **ILIKE** substring matching instead of full-text search. Filter: `or_("title.ilike.%term%,description.ilike.%term%,resolution_note.ilike.%term%")` so that the term is matched in any of those columns.
  - The search term is escaped for ILIKE: backslash to double backslash, `%` to `\%`, `_` to `\_`.
  - Because the builder after `.or_()` does not support `.order()`/`.range()` in this client, results are **sorted and paginated in Python**: sort by `helpful_votes` DESC, then `resolved_at` DESC (fallback `created_at`); then slice `rows[offset : offset + PAGE_SIZE]`. `total_count` is the length of the filtered list before pagination.
- **When `search` is absent:**
  - PostgREST ordering and range are used: `.order("helpful_votes", desc=True).order("resolved_at", desc=True).range(offset, offset + PAGE_SIZE - 1)`. `total_count` comes from `res.count` when available.
- **Category:** If `category` is provided, `.eq("category", category)` is applied in both paths.
- **Response:** Each row has `student` replaced by a flat `student_name`. Response shape: `{ success: true, data: items, page, page_size, total_count }`. Errors return `400` with `{ success: false, message }`.

**Post-launch fixes (search and filter):**

1. **SyncQueryRequestBuilder has no attribute `order`**
   - When search was used, the code previously chained `.text_search(...).order(...).range(...)`. The Supabase/PostgREST client returns a builder type from `.text_search()` that does not support `.order()`, which caused `'SyncQueryRequestBuilder' object has no attribute 'order'`.
   - **Fix:** For the search path, do not call `.order()` or `.range()` on the query. Execute the filtered query, then sort and paginate in Python.

2. **Search filter not returning correct results (e.g. "uni" returning nothing)**
   - The original implementation used PostgreSQL full-text search (`text_search("search_vector", search, options={"type": "websearch"})`). Short or partial terms (e.g. "uni") are often not matched or stemmed correctly (e.g. to "unit", "university"), so users saw no results even when matching rows existed.
   - **Fix:** Replace full-text search with **ILIKE-based** matching. When `search` is present, apply a single `.or_()` filter so that the term is matched as a substring in `title`, `description`, or `resolution_note`. This gives predictable substring behavior (e.g. "uni" matches "unit", "university"). ILIKE special characters in the user input are escaped so the term is interpreted literally.

---

### 3. Frontend API Utilities (Knowledge Base + Helpful Votes)

**File:** `client/src/lib/knowledgeBaseApi.ts`

Shared `API_URL`:

- `const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";`

Exports:

1. `fetchKnowledgeBase({ courseId, search, category, page, token })`
   - Builds query string:
     - `course_id` (required)
     - `page` (default 1)
     - `search` (optional)
     - `category` (optional)
   - GET `GET ${API_URL}/knowledge-base?{params}`
   - Headers: `Authorization: Bearer {token}`
   - Returns `res.json()` with shape:
     - `{ success, data: KnowledgeBaseItem[], page, page_size, total_count, message? }`

2. `fetchSimilarQuestions({ courseId, title, token })`
   - Builds params:
     - `course_id`, `title`.
   - GET `GET ${API_URL}/knowledge-base/similar?{params}`
   - Headers: `Authorization: Bearer {token}`
   - Returns `res.json()` with `data` from the `find_similar_questions` RPC.

3. `markQuestionHelpful({ questionId, token })`
   - POST `POST ${API_URL}/questions/{questionId}/helpful`
   - Headers: `Authorization: Bearer {token}`
   - Returns `res.json()` with:
     - On success: `{ success: true, data: { id, helpful_votes, ... } }`
     - On duplicate: `{ success: false, message: "Already voted helpful" }`.

---

### 4. Student Similar Questions Panel – UX & State

**Files:**

- `client/src/components/questions/QuestionSubmissionForm.tsx`
- `client/src/components/questions/SimilarQuestionsPanel.tsx`
- `client/src/app/sessions/[id]/page.tsx` (for `courseId` wiring)

#### 4.1 `QuestionSubmissionForm` changes

Props extended:

- Original:
  - `sessionId: string`
  - `onSuccess: () => void`
  - `activeQuestion: any | null`
  - `onWithdraw: (id: string) => void`
- New:
  - `courseId?: string` (optional; required for similar-questions functionality).

New imports:

- `useCallback` from React.
- `SimilarQuestionsPanel` from `./SimilarQuestionsPanel`.
- `fetchSimilarQuestions` from `@/lib/knowledgeBaseApi`.

New local state:

- `showSimilarPanel` – `boolean`, default `true`.
- `similarLoading` – `boolean`.
- `similarError` – `string | null`.
- `similarQuestions` – `any[]`.
- `debounceTimer` – `NodeJS.Timeout | null` (for debouncing title input).

Helper: `maybeFetchSimilar(currentTitle: string)` (wrapped in `useCallback`):

- Preconditions:
  - If **no** `token` OR **no** `courseId` OR `!showSimilarPanel` OR `currentTitle.length <= 5`:
    - Clear `similarQuestions`, `similarError`, and `similarLoading` and return.
- Otherwise:
  - `setSimilarLoading(true)` and `setSimilarError(null)`.
  - Call `fetchSimilarQuestions({ courseId, title: currentTitle, token })`.
  - On success: if `res.success && Array.isArray(res.data)` → set `similarQuestions`, else clear.
  - On failure: set `similarError("Could not load similar questions.")`.
  - Always set `similarLoading(false)` in `.finally`.

Debounced `useEffect` on `title`:

- If `!showSimilarPanel`, skip.
- Clears any existing `debounceTimer`.
- Sets a new `setTimeout` (400ms):
  - If `title.length > 5` → invokes `maybeFetchSimilar(title)`.
  - Else → clears `similarQuestions` and `similarError`.
- Stores timer in state and clears on cleanup.

Reset behavior:

- `resetForm()` now also:
  - `setShowSimilarPanel(true)`
  - `setSimilarQuestions([])`
  - `setSimilarError(null)`

Render integration:

- Just above the `<form>`:
  - If `showSimilarPanel && courseId`:
    - Render `<SimilarQuestionsPanel questions={similarQuestions} loading={similarLoading} error={similarError} onDismiss={() => setShowSimilarPanel(false)} />`
  - When dismissed, `showSimilarPanel` becomes false and all fetching stops for the rest of that form lifecycle.

Everything else in the form (validation, submit, edit flow) remains unchanged.

#### 4.2 `SimilarQuestionsPanel` component

**File:** `client/src/components/questions/SimilarQuestionsPanel.tsx`

Props:

- `questions: { id: string; title: string; resolution_note?: string | null; helpful_votes?: number; }[]`
- `loading: boolean`
- `error: string | null`
- `onDismiss: () => void`

Behavior:

- If **not** loading, **no** error, and `questions.length === 0`, returns `null` (nothing rendered).
- Otherwise renders:
  - Cyan-tinted card:
    - Header:
      - Label: “Similar resolved questions”.
      - Supporting text: “These might already answer what you're asking.”
      - **Dismiss** link: calls `onDismiss`.
  - When `loading`: “Searching past questions...” message.
  - When `error`: small red error text.
  - When data:
    - List of question cards:
      - Title (2-line clamp).
      - Resolution note preview (cut to ~140 chars with ellipsis).
      - Optional “N found this helpful” line if `helpful_votes > 0`.

Styling:

- Uses Tailwind theme tokens:
  - `bg-cyan-500/10`, `border-cyan-500/40`, `rounded-card`, `bg-surface/60`, etc., matching the cyan-tinted design in the PRD.

#### 4.3 Wiring `courseId` into `QuestionSubmissionForm`

**File:** `client/src/app/sessions/[id]/page.tsx`

- The `SessionView` already fetches `sessionInfo` from `/sessions/{id}` which contains `course_id`.
- Student view section now passes `courseId`:

```tsx
<QuestionSubmissionForm
  sessionId={sessionId}
  onSuccess={fetchSessionAndQuestions}
  activeQuestion={activeQuestion}
  onWithdraw={(id) => handleAction("withdraw", id)}
  courseId={sessionInfo?.course_id}
/>
```

This enables similar-questions queries to be correctly scoped to the course.

---

### 5. Knowledge Base Browse/Search Page – Routing & Layout

**File:** `client/src/app/courses/[id]/knowledge-base/page.tsx`

Component: `CourseKnowledgeBasePage`

Key behavior:

- Reads `courseId` via `useParams()`.
- Reads `user` and `token` from `useAuth()`.

Local state:

- `items: KnowledgeBaseItem[]`
- `loading: boolean`
- `error: string | null`
- `search: string`, `debouncedSearch: string`
- `category: string` (empty string means “all”)
- `page: number`
- `totalCount: number`
- `PAGE_SIZE = 20` (mirrors backend).

Debounced search:

- `useEffect` on `search`:
  - After 400ms of no typing, sets `debouncedSearch = search.trim()` and resets `page` to 1.

Data loading effect:

- `useEffect` on `[token, courseId, debouncedSearch, category, page]`:
  - If no `token` or no `courseId`, early-return.
  - Sets `loading` true and `error` null.
  - Calls `fetchKnowledgeBase({ courseId, search: debouncedSearch || undefined, category: category || undefined, page, token })`.
  - On success:
    - `setItems(res.data || [])`
    - `setTotalCount(res.total_count ?? (res.data ? res.data.length : 0))`
  - On failure:
    - `setError(res.message || "Failed to load knowledge base")` or `"Network error loading knowledge base"`.
  - Finally sets `loading` false.

Layout:

- Uses `NavBar` at the top.
- Main section, `max-w-3xl mx-auto`.
- Header:
  - `h1` “Knowledge Base”.
  - Subtext: “Browse resolved questions from this course's past sessions.”

Controls card:

- Search:
  - Text input bound to `search`.
  - Debounced through `debouncedSearch` effect.
- Category dropdown:
  - Options: All, Debugging, Conceptual, Environment Setup, Assignment Help, Other.
  - When changed:
    - `setCategory(e.target.value); setPage(1);`
- Results summary:
  - If `totalCount > 0`, shows:
    - `Showing (page-1)*PAGE_SIZE+1 – min(page*PAGE_SIZE, totalCount) of totalCount`.

Result rendering:

- If `loading`: text “Loading knowledge base...”.
- If `error && !loading`: red error banner.
- If `!loading && !error && items.length === 0`: empty-state card.
- Else:
  - For each `item`:
    - Card with:
      - Title.
      - Category badge with color per PRD:
        - `debugging` → purple.
        - `setup` → cyan.
        - `conceptual` → green.
        - `assignment` → amber.
        - `other` → red.
      - Student name: “Asked by {student_name}” if available.
      - Resolved date: formatted using `new Date(resolved_at).toLocaleDateString()`.
      - Resolution note preview:
        - Up to ~260 chars with ellipsis.
      - **Helpful vote button** (see next section).

Pagination:

- `totalPages = totalCount > 0 ? Math.ceil(totalCount / PAGE_SIZE) : page;`
- Renders Prev/Next buttons:
  - Prev disabled when `page <= 1`.
  - Next disabled when `page >= totalPages`.
- Center shows “Page X of Y”.

---

### 6. Helpful Vote Button – Frontend Behavior

**File:** `client/src/components/questions/HelpfulVoteButton.tsx`

Imports:

- `useState` from React.
- `Sparkles` icon from `lucide-react`.
- `useAuth` for token.
- `markQuestionHelpful` from `@/lib/knowledgeBaseApi`.

Props:

- `questionId: string`
- `initialCount: number`

Internal state:

- `count` – initialized from `initialCount`.
- `hasVoted` – `false` initially.
- `loading` – `false` initially.
- `error` – `string | null`.

Click handler:

- If `!token` or `hasVoted` or `loading`, returns immediately (no-op).
- Sets `loading(true)` and `error(null)`.
- Calls `markQuestionHelpful({ questionId, token })`.
- Response handling:
  - If `res.success`:
    - If `res.data` has numeric `helpful_votes`, use that:
      - `setCount(res.data.helpful_votes)`.
    - Else fallback: `setCount(prev => prev + 1)`.
    - `setHasVoted(true)`.
  - Else if `res.message === "Already voted helpful"`:
    - `setHasVoted(true)` (count unchanged).
  - Else:
    - `setError(res.message || "Could not record vote")`.
- On network error:
  - `setError("Network error")`.
- Finally:
  - `setLoading(false)`.

Render:

- Button:
  - Disabled if `loading || hasVoted`.
  - Visual states:
    - When voted:
      - `bg-green/10 border-green/40 text-green`.
      - Label: “Marked helpful”.
    - When not yet voted:
      - `bg-surface border-border text-text-secondary` with hover changes.
  - Inside:
    - `Sparkles` icon.
    - Label text.
    - Count: `· {count}`.
- Error text:
  - If `error`, show small red message below.

Integration:

- In `CourseKnowledgeBasePage`:

```tsx
<HelpfulVoteButton
  questionId={item.id}
  initialCount={item.helpful_votes || 0}
/>
```

---

### 7. Navigation to Knowledge Base (No Manual URLs)

**Course detail page:** `client/src/app/courses/[id]/page.tsx`

- Header updated to include a **Knowledge Base** button:

```tsx
<div className="flex flex-wrap items-center gap-3">
  <Link
    href={`/courses/${courseId}/knowledge-base`}
    className="px-4 py-2 rounded-input border border-border text-sm font-medium text-text-secondary hover:text-text-primary hover:border-text-muted transition-colors"
  >
    Knowledge Base
  </Link>
  {user?.role === "professor" && (
    // existing Create Session button...
  )}
</div>
```

- Visible to any authenticated user who can see the course.
- Works regardless of whether there are any sessions / resolved questions (empty state handled by KB page).

**Session view:** `client/src/app/sessions/[id]/page.tsx`

- Under the session header, if `sessionInfo.course_id` exists, show:

```tsx
{sessionInfo?.course_id && (
  <div className="mt-2">
    <Link
      href={`/courses/${sessionInfo.course_id}/knowledge-base`}
      className="text-xs text-text-muted underline-offset-2 hover:underline hover:text-text-primary"
    >
      View course knowledge base
    </Link>
  </div>
)}
```

This gives both students and staff a contextual route from a live session directly into the course’s knowledge base.

---

### 8. Testing Notes

**Manual testing flows:**

1. **Similar questions panel**
   - Log in as a student.
   - Go to `/dashboard` → select a course → select an **active** session.
   - In the “Ask a Question” form:
     - Type a title with more than 5 characters.
     - Confirm the cyan “Similar resolved questions” panel appears.
     - Confirm matching resolved questions are shown (assuming data exists).
     - Click “Dismiss” and ensure the panel does not reappear while continuing to type.
     - Submit a question normally; ensure behavior is unchanged.

2. **Knowledge base page**
   - From the dashboard:
     - Click a course → `/courses/[id]`.
     - Click **“Knowledge Base”**.
     - Verify:
       - Search input filters results.
       - Category dropdown filters results.
       - Pagination works when `total_count > 20`.
       - Empty state appears when no resolved questions exist.

3. **Helpful votes**
   - On the knowledge base page, choose a resolved question.
   - Click **“Mark helpful”**:
     - Button switches to “Marked helpful”.
     - Count increases appropriately (or matches backend count).
   - Click again:
     - No further increase; backend returns “Already voted helpful”.
     - Button stays in the voted state.

4. **Navigation**
   - From **dashboard** → **course** → **Knowledge Base**:
     - Confirm no manual URL typing is necessary.
   - From **session view** → **View course knowledge base**:
     - Confirm link navigates to `/courses/[courseId]/knowledge-base`.

