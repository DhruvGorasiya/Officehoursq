# Issue #12 — Supabase Realtime Progress

## 1. Scope of Issue #12

**Goal:** Implement real-time updates using Supabase Realtime so that:

- TA + professor queue views, and student queue status update instantly on changes.
- Session status changes propagate to connected clients.
- User-specific notifications are pushed to the appropriate user.

This issue builds on:

- Sprint 1 backend (`FastAPI` + `Postgres`): `auth`, `courses`, `sessions`, `questions`.
- Issue #11 TA queue UI: TA view in `SessionView` is already implemented and uses `questions` for stats + cards.

Realtime is implemented as **event → backend broadcast → Supabase channel → frontend subscription → refetch**.

---

## 2. Backend Realtime Implementation

### 2.1 Supabase client & config (server)

- `server/app/core/config.py`
  - Already had Supabase envs:
    - `SUPABASE_URL`
    - `SUPABASE_KEY`
    - `SUPABASE_SERVICE_ROLE_KEY`
- `server/app/core/database.py`
  - Creates a global Supabase client:
    - `supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)`

Supabase client is used both for DB calls and for realtime broadcasts (via `supabase.realtime`).

### 2.2 Realtime broadcast helpers

- **File:** `server/app/utils/realtime_broadcast.py`
- Provides three helpers:

```python
def broadcast_session_event(session_id: str, event: str, payload: dict) -> None:
    # Channel: session:{session_id}

def broadcast_user_notification(user_id: str, payload: dict) -> None:
    # Channel: user:{user_id}, event: notification:new

def broadcast_course_session_status(course_id: str, payload: dict) -> None:
    # Channel: course:{course_id}, event: session:updated
```

Implementation notes:

- All helpers call an internal `_safe_broadcast(channel, event, payload)`:
  - Uses `supabase.realtime.broadcast` if available.
  - Swallows exceptions (best-effort; never breaks request handler).

### 2.3 Question lifecycle hooks

- **File:** `server/app/api/routes/questions.py`

Existing functions still use Supabase table APIs for data changes. Realtime is layered on **after** successful DB updates.

Changes per endpoint:

- `POST /api/questions` (`create_question`)
  - After insert:
    - `created = res.data[0]`
    - Broadcasts:
      - `broadcast_session_event(session_id, "question:submitted", {"question": created})`

- `PATCH /api/questions/{id}/claim` (`claim_question`)
  - After update:
    - `updated = res.data[0]`
    - Broadcasts:
      - `broadcast_session_event(session_id, "question:claimed", {"question": updated})`
      - If `student_id` present:
        - `broadcast_user_notification(student_id, {"type": "question_claimed", "question_id": ..., "session_id": ...})`

- `PATCH /api/questions/{id}/resolve` (`resolve_question`)
  - After update + `recalculate_queue(session_id)`:
    - `updated = res.data[0]`
    - Broadcasts:
      - `broadcast_session_event(session_id, "question:resolved", {"question": updated})`
      - Notification to student: `type = "question_resolved"`.

- `PATCH /api/questions/{id}/defer` (`defer_question`)
  - After update + `recalculate_queue(session_id)`:
    - `updated = res.data[0]`
    - Broadcasts:
      - `broadcast_session_event(session_id, "question:deferred", {"question": updated})`
      - Notification: `type = "question_deferred"`.

- `PATCH /api/questions/{id}/withdraw` (`withdraw_question`)
  - After update + `recalculate_queue(session_id)`:
    - `updated = res.data[0]`
    - Broadcasts:
      - `broadcast_session_event(session_id, "question:withdrawn", {"question": updated})`

**Important:** Queue logic remains unchanged; realtime just publishes after the existing logic runs.

### 2.4 Session status hooks

- **File:** `server/app/api/routes/sessions.py`
- Endpoint: `PATCH /api/sessions/{id}/status` (`update_session_status`)

After validating transitions and applying side effects (e.g.:

- `scheduled -> active` (checking for another active session).
- `active -> ended` (marking `queued`/`in_progress`/`deferred` as `unresolved`)).

…the code now:

```python
res = supabase.table("sessions").update({"status": new_status}).eq("id", session_id).execute()
updated = res.data[0]

broadcast_course_session_status(course_id, {"session": updated})
broadcast_session_event(session_id, "session:updated", {"session": updated})
```

So both course-level and session-level subscribers are informed.

---

## 3. Frontend Realtime Implementation

### 3.1 Supabase browser client

- **File:** `client/src/lib/supabaseClient.ts`

```ts
import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL as string | undefined;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string | undefined;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn("Supabase env vars are not configured; realtime features will be disabled.");
}

export const supabaseClient =
  SUPABASE_URL && SUPABASE_ANON_KEY
    ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
    : null;
```

If env vars are missing, `supabaseClient` is `null` and realtime hooks become no-ops (app still works via polling).

### 3.2 Generic realtime hook

- **File:** `client/src/hooks/useRealtimeChannel.ts`

```ts
type QuestionEventHandler = (payload: any) => void;
type SessionEventHandler = (payload: any) => void;
type NotificationEventHandler = (payload: any) => void;

interface RealtimeHandlers {
  onQuestionEvent?: QuestionEventHandler;
  onSessionEvent?: SessionEventHandler;
  onNotificationEvent?: NotificationEventHandler;
}

export function useRealtimeChannel(channelName: string | null, handlers: RealtimeHandlers) {
  useEffect(() => {
    if (!channelName || !supabaseClient) return;

    const channel = supabaseClient.channel(channelName);

    if (handlers.onQuestionEvent) {
      channel.on("broadcast", { event: "question:submitted" }, (p) => handlers.onQuestionEvent?.(p.payload));
      channel.on("broadcast", { event: "question:claimed" }, (p) => handlers.onQuestionEvent?.(p.payload));
      channel.on("broadcast", { event: "question:resolved" }, (p) => handlers.onQuestionEvent?.(p.payload));
      channel.on("broadcast", { event: "question:deferred" }, (p) => handlers.onQuestionEvent?.(p.payload));
      channel.on("broadcast", { event: "question:withdrawn" }, (p) => handlers.onQuestionEvent?.(p.payload));
    }

    if (handlers.onSessionEvent) {
      channel.on("broadcast", { event: "session:updated" }, (p) => handlers.onSessionEvent?.(p.payload));
    }

    if (handlers.onNotificationEvent) {
      channel.on("broadcast", { event: "notification:new" }, (p) => handlers.onNotificationEvent?.(p.payload));
    }

    channel.subscribe();
    return () => channel.unsubscribe();
  }, [channelName, handlers.onQuestionEvent, handlers.onSessionEvent, handlers.onNotificationEvent]);
}
```

This abstracts Supabase Realtime so pages just pass `channelName` + simple handlers.

### 3.3 SessionView realtime (queue + student view)

- **File:** `client/src/app/sessions/[id]/page.tsx`

Key points:

- `SessionView` already had:
  - `fetchSessionAndQuestions()` for `/sessions/{id}` + `/questions?session_id=...`.
  - A 10-second polling `useEffect` as a fallback.
- Now it also calls:

```ts
useRealtimeChannel(
  sessionId ? `session:${sessionId}` : null,
  {
    onQuestionEvent: () => {
      fetchSessionAndQuestions();
    },
    onSessionEvent: () => {
      fetchSessionAndQuestions();
    },
  }
);
```

Effects:

- **Student view:** queue status card (position, ETA, claimed/deferred messaging) updates as soon as:
  - Their question is submitted/claimed/resolved/deferred/withdrawn.
- **TA view:** stats row + queue cards update on every question event and session status event.
- Polling remains as a safety net; realtime just reduces the delay.

---

## 4. Notifications Realtime Integration

### 4.1 Auth context changes

- **File:** `client/src/context/AuthContext.tsx`

Additions:

- `unreadCount` in context:

```ts
interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  unreadCount: number;
  login: (...);
  logout: () => void;
  revalidate: () => Promise<void>;
}
```

- State + logout reset:

```ts
const [unreadCount, setUnreadCount] = useState(0);

const logout = () => {
  localStorage.removeItem("token");
  setToken(null);
  setUser(null);
  setUnreadCount(0);
  router.push("/login");
};
```

- Realtime subscription on `user:{user.id}`:

```ts
useRealtimeChannel(
  user ? `user:${user.id}` : null,
  {
    onNotificationEvent: () => {
      setUnreadCount((prev) => prev + 1);
    },
  }
);
```

### 4.2 NavBar bell badge

- **File:** `client/src/components/common/NavBar.tsx`

Changes:

- Reads `unreadCount` from `useAuth()`:

```ts
const { user, logout, unreadCount } = useAuth();
```

- Renders badge only when `unreadCount > 0`:

```tsx
<button className="relative text-text-secondary hover:text-text-primary transition-colors">
  <Bell className="w-5 h-5" />
  {unreadCount > 0 && (
    <span className="absolute -top-1 -right-1 flex h-4 min-w-4 px-1 items-center justify-center rounded-badge bg-red text-[10px] font-bold text-white">
      {unreadCount > 9 ? "9+" : unreadCount}
    </span>
  )}
</button>
```

This provides a simple unread count UI for realtime notifications.

---

## 5. Testing Summary (What Works Now)

With Issue #12 implemented and Supabase env vars configured:

- **Student** and **TA/professor** on the same session see:
  - New questions appear in TA queue immediately (no manual refresh).
  - Claims, resolves, defers, and withdraws propagate instantly to both queue and student status card.
- **Professor / course view**:
  - Session status changes (start/end) broadcast to `course:{courseId}` and `session:{sessionId}`; once a course/session page subscribes, it can react without polling.
- **Notifications**:
  - When TA actions trigger `broadcast_user_notification`, the target student’s bell unread count increases live.

Fallback:

- If Supabase env vars are missing or Realtime is down, the 10-second polling loop in `SessionView` still keeps the UI approximately up-to-date.

---

## 6. Suggested Next Steps for Issue #13

When working on **Issue #13** (knowledge base / similar questions / analytics, depending on the PRD), you can assume:

- Realtime event channels and naming are established:
  - `session:{id}` for queue and session events.
  - `user:{id}` for notifications.
  - `course:{id}` for session status changes.
- A simple pattern for “event arrives → refetch primary data” is in place via `useRealtimeChannel`.

For any new realtime-dependent feature in Issue #13:

- Reuse `useRealtimeChannel` and/or extend it with specific event handlers.
- Prefer to keep core state ownership in page-level components (like `SessionView`) and trigger **refetch** on events, rather than trying to maintain complex in-memory diffs, unless performance becomes an issue.***
