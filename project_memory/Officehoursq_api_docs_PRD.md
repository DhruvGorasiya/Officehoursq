# OfficeHoursQ: API Documentation Task

## WHAT THIS TASK IS

Annotate the existing FastAPI codebase so that FastAPI's built-in `/docs` (Swagger UI) and `/redoc` (ReDoc) endpoints produce complete, professional API documentation. This means modifying existing Python files, NOT creating markdown files.

## WHAT THIS TASK IS NOT

- Do NOT create any `.md` documentation files.
- Do NOT create a separate OpenAPI YAML or JSON file.
- Do NOT install swagger-jsdoc, swagger-ui-express, or any Node.js documentation packages.
- Do NOT write prose documentation. The documentation IS the code annotations.

FastAPI generates OpenAPI docs automatically from your route decorators and Pydantic models. Your only job is to make sure every route and schema is properly annotated.

---

## PROJECT STRUCTURE (existing files to modify)

```
server/
├── main.py (or app.py)           # FastAPI app initialization
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py           # Auth endpoints
│   │       ├── courses.py        # Course endpoints
│   │       ├── sessions.py       # Session endpoints
│   │       ├── questions.py      # Question endpoints
│   │       ├── notifications.py  # Notification endpoints
│   │       ├── knowledge_base.py # Knowledge base endpoints
│   │       └── analytics.py      # Analytics endpoints
│   ├── schemas/
│   │   ├── auth.py               # Auth Pydantic models
│   │   ├── common.py             # Shared models (SuccessResponse, ErrorResponse)
│   │   └── ...                   # Other schema files
│   ├── models/                   # Database models
│   ├── core/
│   │   └── deps.py               # Dependencies (get_current_user, require_role)
│   └── services/                 # Business logic
```

**IMPORTANT:** Before starting, run `find server/ -name "*.py" | head -50` to confirm the actual file paths. If the structure differs from above, adapt accordingly. The key point is: modify the existing files, do not create new markdown or documentation files.

---

## TASK 1: Update FastAPI App Metadata

**File to modify:** The file where `FastAPI()` is instantiated (likely `server/main.py` or `server/app/main.py`).

**What to do:** Add metadata parameters to the `FastAPI()` constructor.

**Before (likely current state):**

```python
app = FastAPI()
```

**After:**

```python
app = FastAPI(
    title="OfficeHoursQ API",
    description=(
        "Real-time office hours queue management API for university courses. "
        "Supports three user roles: Student, TA, and Professor. "
        "Features include question queue management, real-time updates via Supabase Realtime, "
        "knowledge base search, and analytics dashboards."
    ),
    version="1.0.0",
    contact={"name": "OfficeHoursQ Team"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "Auth", "description": "User registration, login, and authentication"},
        {"name": "Courses", "description": "Course creation, enrollment, and management"},
        {"name": "Sessions", "description": "Office hours session scheduling and lifecycle"},
        {"name": "Questions", "description": "Question submission, claiming, resolving, and queue management"},
        {"name": "Knowledge Base", "description": "Search resolved questions and find similar past questions"},
        {"name": "Analytics", "description": "Professor-only dashboards: overview, categories, trends, TA performance"},
        {"name": "Notifications", "description": "User notification retrieval and read status management"},
    ],
)
```

**Verify:** Run the server and visit `/docs`. You should see the title, description, and tag groupings.

---

## TASK 2: Ensure All Pydantic Schemas Exist and Have Field Descriptions

**Files to modify:** Files inside `server/app/schemas/` (create new schema files only if a schema group doesn't exist yet, e.g., `schemas/questions.py`, `schemas/sessions.py`, `schemas/analytics.py`, `schemas/notifications.py`, `schemas/knowledge_base.py`).

**What to do:** Make sure every request body and response body used by any endpoint has a Pydantic model with `Field()` descriptions. If schemas already exist, ADD the `description` parameter to each field. If schemas don't exist for some endpoint groups, create them as `.py` files in the `schemas/` directory.

Below are ALL the schemas needed. For each one, check if it already exists. If yes, add `description=` to each field. If no, create it.

### Enums (likely in `schemas/common.py` or `schemas/enums.py`)

```python
from enum import Enum

class UserRole(str, Enum):
    student = "student"
    ta = "ta"
    professor = "professor"

class SessionStatus(str, Enum):
    scheduled = "scheduled"
    active = "active"
    ended = "ended"

class RecurringPattern(str, Enum):
    weekly = "weekly"
    biweekly = "biweekly"

class QuestionCategory(str, Enum):
    debugging = "debugging"
    conceptual = "conceptual"
    setup = "setup"
    assignment = "assignment"
    other = "other"

class QuestionPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class QuestionStatus(str, Enum):
    queued = "queued"
    in_progress = "in_progress"
    resolved = "resolved"
    deferred = "deferred"
    withdrawn = "withdrawn"
    unresolved = "unresolved"

class NotificationType(str, Enum):
    question_claimed = "question_claimed"
    question_resolved = "question_resolved"
    question_deferred = "question_deferred"
    question_submitted = "question_submitted"
    session_active = "session_active"
    session_starting = "session_starting"
```

### Auth Schemas (in `schemas/auth.py`)

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr = Field(description="User's email address")
    password: str = Field(min_length=8, description="Password, minimum 8 characters")
    name: str = Field(max_length=100, description="User's display name")
    role: UserRole = Field(description="User role: student, ta, or professor")

class LoginRequest(BaseModel):
    email: EmailStr = Field(description="Registered email address")
    password: str = Field(description="Account password")

class UserResponse(BaseModel):
    id: UUID = Field(description="Unique user identifier")
    email: str = Field(description="User's email")
    name: str = Field(description="User's display name")
    role: UserRole = Field(description="User's role")
    created_at: datetime = Field(description="Account creation timestamp")
```

### Course Schemas (in `schemas/courses.py`, create if missing)

```python
class CreateCourseRequest(BaseModel):
    name: str = Field(max_length=200, description="Course name, e.g. 'CS5340 - HCI'")

class JoinCourseRequest(BaseModel):
    invite_code: str = Field(min_length=6, max_length=6, description="6-character alphanumeric invite code")

class CourseResponse(BaseModel):
    id: UUID = Field(description="Course ID")
    name: str = Field(description="Course name")
    invite_code: str = Field(description="6-char invite code for joining")
    professor_id: UUID = Field(description="ID of the professor who owns the course")
    created_at: datetime = Field(description="Creation timestamp")
```

### Session Schemas (in `schemas/sessions.py`, create if missing)

```python
from typing import List, Optional

class CreateSessionRequest(BaseModel):
    course_id: UUID = Field(description="ID of the course this session belongs to")
    title: str = Field(max_length=200, description="Session title, e.g. 'Midterm Review'")
    date: str = Field(description="Session date in ISO format")
    start_time: str = Field(description="Start time in ISO format")
    end_time: str = Field(description="End time in ISO format")
    ta_ids: List[UUID] = Field(default=[], description="List of TA user IDs assigned to this session")
    topics: List[str] = Field(default=[], description="List of topic strings for this session")
    is_recurring: bool = Field(default=False, description="Whether this session recurs")
    recurring_pattern: Optional[RecurringPattern] = Field(default=None, description="Recurrence pattern: weekly or biweekly")

class UpdateSessionRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Updated session title")
    date: Optional[str] = Field(None, description="Updated date")
    start_time: Optional[str] = Field(None, description="Updated start time")
    end_time: Optional[str] = Field(None, description="Updated end time")
    ta_ids: Optional[List[UUID]] = Field(None, description="Updated TA assignments")
    topics: Optional[List[str]] = Field(None, description="Updated topics list")
    is_recurring: Optional[bool] = Field(None, description="Updated recurrence flag")
    recurring_pattern: Optional[RecurringPattern] = Field(None, description="Updated recurrence pattern")

class UpdateSessionStatusRequest(BaseModel):
    status: SessionStatus = Field(description="New status. Valid transitions: scheduled->active, active->ended")

class SessionResponse(BaseModel):
    id: UUID = Field(description="Session ID")
    course_id: UUID = Field(description="Parent course ID")
    title: str = Field(description="Session title")
    date: str = Field(description="Session date")
    start_time: str = Field(description="Start time")
    end_time: str = Field(description="End time")
    status: SessionStatus = Field(description="Current status")
    topics: List[str] = Field(description="Session topics")
    is_recurring: bool = Field(description="Recurrence flag")
    recurring_pattern: Optional[RecurringPattern] = Field(description="Recurrence pattern")
    created_by: UUID = Field(description="Professor who created the session")
    created_at: datetime = Field(description="Creation timestamp")
```

### Question Schemas (in `schemas/questions.py`, create if missing)

```python
class CreateQuestionRequest(BaseModel):
    session_id: UUID = Field(description="ID of the active session to submit to")
    title: str = Field(max_length=200, description="Brief summary of the issue")
    description: str = Field(max_length=2000, description="Detailed problem description")
    code_snippet: Optional[str] = Field(None, max_length=5000, description="Relevant code, optional")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error output, optional")
    what_tried: str = Field(max_length=2000, description="What the student has already attempted")
    category: QuestionCategory = Field(description="Question category")
    priority: QuestionPriority = Field(description="Self-assessed priority")

class UpdateQuestionRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Updated title")
    description: Optional[str] = Field(None, max_length=2000, description="Updated description")
    code_snippet: Optional[str] = Field(None, max_length=5000, description="Updated code snippet")
    error_message: Optional[str] = Field(None, max_length=1000, description="Updated error message")
    what_tried: Optional[str] = Field(None, max_length=2000, description="Updated troubleshooting notes")
    category: Optional[QuestionCategory] = Field(None, description="Updated category")
    priority: Optional[QuestionPriority] = Field(None, description="Updated priority")

class ResolveQuestionRequest(BaseModel):
    resolution_note: str = Field(max_length=2000, description="How the question was resolved")

class DeferQuestionRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=2000, description="Optional note explaining the deferral")

class QuestionResponse(BaseModel):
    id: UUID = Field(description="Question ID")
    session_id: UUID = Field(description="Session this question belongs to")
    course_id: UUID = Field(description="Course this question belongs to")
    student_id: UUID = Field(description="ID of the student who submitted")
    title: str = Field(description="Question title")
    description: str = Field(description="Full description")
    code_snippet: Optional[str] = Field(description="Code snippet if provided")
    error_message: Optional[str] = Field(description="Error message if provided")
    what_tried: str = Field(description="What the student tried")
    category: QuestionCategory = Field(description="Question category")
    priority: QuestionPriority = Field(description="Question priority")
    status: QuestionStatus = Field(description="Current status in the queue lifecycle")
    claimed_by_ta_id: Optional[UUID] = Field(description="ID of the TA who claimed this, if any")
    resolution_note: Optional[str] = Field(description="Resolution details, if resolved")
    helpful_votes: int = Field(description="Number of helpful votes from students")
    submitted_at: datetime = Field(description="When the question was submitted")
    claimed_at: Optional[datetime] = Field(description="When a TA claimed the question")
    resolved_at: Optional[datetime] = Field(description="When the question was resolved")
    deferred_at: Optional[datetime] = Field(description="When the question was last deferred")
```

### Knowledge Base Schemas (in `schemas/knowledge_base.py`, create if missing)

```python
class SimilarQuestionResponse(BaseModel):
    id: UUID = Field(description="Question ID")
    title: str = Field(description="Question title")
    resolution_note: Optional[str] = Field(description="How it was resolved")
    helpful_votes: int = Field(description="Number of helpful votes")
    resolved_at: Optional[datetime] = Field(description="When it was resolved")
```

### Analytics Schemas (in `schemas/analytics.py`, create if missing)

```python
class OverviewResponse(BaseModel):
    total_questions: int = Field(description="Total questions across all sessions")
    avg_wait_minutes: float = Field(description="Average wait time in minutes")
    avg_resolve_minutes: float = Field(description="Average resolution time in minutes")
    recent_sessions: List[dict] = Field(description="List of recent session summaries")

class CategoryBreakdown(BaseModel):
    category: QuestionCategory = Field(description="Question category")
    count: int = Field(description="Number of questions in this category")
    percentage: float = Field(description="Percentage of total questions")

class WeeklyTrend(BaseModel):
    week: str = Field(description="Week label, e.g. 'W1', 'W2'")
    question_count: int = Field(description="Number of questions that week")

class TAPerformance(BaseModel):
    ta_id: UUID = Field(description="TA's user ID")
    ta_name: str = Field(description="TA's display name")
    resolved_count: int = Field(description="Total questions resolved by this TA")
    avg_resolve_minutes: float = Field(description="Average time to resolve in minutes")
    rating: Optional[float] = Field(description="Average helpful rating, if available")
```

### Notification Schemas (in `schemas/notifications.py`, create if missing)

```python
class NotificationResponse(BaseModel):
    id: UUID = Field(description="Notification ID")
    user_id: UUID = Field(description="Recipient user ID")
    type: NotificationType = Field(description="Notification type")
    message: str = Field(description="Human-readable notification message")
    related_question_id: Optional[UUID] = Field(description="Related question, if applicable")
    related_session_id: Optional[UUID] = Field(description="Related session, if applicable")
    is_read: bool = Field(description="Whether the user has read this notification")
    created_at: datetime = Field(description="When the notification was created")

class UnreadCountResponse(BaseModel):
    count: int = Field(description="Number of unread notifications")
```

### Standard Wrappers (in `schemas/common.py`)

```python
from typing import TypeVar, Generic, Any
from pydantic import BaseModel, Field

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True, description="Always true for successful responses")
    data: T = Field(description="Response payload")

class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Always false for error responses")
    message: str = Field(description="Human-readable error message")
```

**Verify:** After this task, all schema files should have `Field(description=...)` on every field.

---

## TASK 3: Annotate Every Route Decorator

**Files to modify:** Every file in `server/app/api/routes/`.

**What to do:** Add `tags`, `summary`, `description`, `response_model`, and `responses` parameters to every `@router.get()`, `@router.post()`, `@router.patch()`, `@router.put()`, `@router.delete()` decorator.

Below is the exact annotation for EVERY endpoint. Find the matching route in the codebase and add these parameters to its decorator. Do NOT change the function body or business logic, only the decorator.

### Auth Routes (`routes/auth.py`)

```python
@router.post(
    "/api/auth/register",
    tags=["Auth"],
    summary="Register a new user",
    description="Create a new account with email, password, name, and role. Returns a JWT token and user object.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Email already registered, or validation error"},
    },
)

@router.post(
    "/api/auth/login",
    tags=["Auth"],
    summary="Login with email and password",
    description="Authenticate with email and password. Returns a JWT token and user object.",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid email or password"},
    },
)

@router.get(
    "/api/auth/me",
    tags=["Auth"],
    summary="Get current user",
    description="Returns the authenticated user's profile. Requires a valid JWT Bearer token.",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid JWT token"},
    },
)
```

### Course Routes (`routes/courses.py`)

```python
@router.post(
    "/api/courses",
    tags=["Courses"],
    summary="Create a new course",
    description="Professor creates a new course. An invite code is auto-generated. Only users with the professor role can call this.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a professor"},
    },
)

@router.get(
    "/api/courses",
    tags=["Courses"],
    summary="List enrolled or owned courses",
    description="Returns all courses the authenticated user is enrolled in (as student or TA) or owns (as professor).",
    response_model=SuccessResponse,
)

@router.get(
    "/api/courses/{id}",
    tags=["Courses"],
    summary="Get course by ID",
    description="Returns course details. User must be enrolled in the course or be the owning professor.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not enrolled in this course"},
        404: {"model": ErrorResponse, "description": "Course not found"},
    },
)

@router.post(
    "/api/courses/join",
    tags=["Courses"],
    summary="Join a course by invite code",
    description="Student or TA joins a course using a 6-character invite code. Fails if already enrolled or code is invalid.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid invite code or already enrolled"},
    },
)
```

### Session Routes (`routes/sessions.py`)

```python
@router.post(
    "/api/sessions",
    tags=["Sessions"],
    summary="Create a new session",
    description="Professor creates an office hours session with title, time, assigned TAs, and topics.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a professor"},
    },
)

@router.get(
    "/api/sessions",
    tags=["Sessions"],
    summary="List sessions for a course",
    description="Returns all sessions for a given course_id. User must be enrolled in the course.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not enrolled in this course"},
    },
)

@router.patch(
    "/api/sessions/{id}/status",
    tags=["Sessions"],
    summary="Change session status",
    description="Professor changes session status. Valid transitions: scheduled to active (fails if another session in the same course is already active), active to ended (marks all remaining queued questions as unresolved and notifies students).",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid status transition, or another session is already active"},
        403: {"model": ErrorResponse, "description": "User is not a professor"},
    },
)

@router.put(
    "/api/sessions/{id}",
    tags=["Sessions"],
    summary="Update a scheduled session",
    description="Professor updates session details. Only allowed when session status is 'scheduled'. Cannot edit active or ended sessions.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Session is not in scheduled status"},
        403: {"model": ErrorResponse, "description": "User is not a professor"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)

@router.delete(
    "/api/sessions/{id}",
    tags=["Sessions"],
    summary="Delete a scheduled session",
    description="Professor deletes a session. Only allowed when status is 'scheduled'. Cannot delete active sessions.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Session is not in scheduled status, or session is active"},
        403: {"model": ErrorResponse, "description": "User is not a professor"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
```

### Question Routes (`routes/questions.py`)

```python
@router.post(
    "/api/questions",
    tags=["Questions"],
    summary="Submit a question to an active session",
    description="Student submits a new question. Fails if the session is not active, or if the student already has an active question (queued or in_progress) in this session. Limit: one active question per student per session.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Session not active, or student already has an active question in this session"},
        403: {"model": ErrorResponse, "description": "User is not a student"},
    },
)

@router.get(
    "/api/questions",
    tags=["Questions"],
    summary="List questions for a session",
    description="Returns all questions for a given session_id. Only TAs and Professors can view the full queue.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a TA or professor"},
    },
)

@router.get(
    "/api/questions/{id}",
    tags=["Questions"],
    summary="Get a single question",
    description="Returns question details. Accessible by the student who submitted it, any TA in the session, or the professor.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User does not have access to this question"},
        404: {"model": ErrorResponse, "description": "Question not found"},
    },
)

@router.put(
    "/api/questions/{id}",
    tags=["Questions"],
    summary="Edit a queued question",
    description="Student edits their own question. Only allowed when the question status is 'queued'. Cannot edit questions that are in_progress, resolved, or withdrawn.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Question is not in queued status"},
        403: {"model": ErrorResponse, "description": "User is not the question owner"},
        404: {"model": ErrorResponse, "description": "Question not found"},
    },
)

@router.patch(
    "/api/questions/{id}/claim",
    tags=["Questions"],
    summary="Claim a question",
    description="TA claims a queued question to start helping. Sets status to in_progress and records claimed_by and claimed_at. Fails if the question is already claimed by another TA.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Question is already claimed"},
        403: {"model": ErrorResponse, "description": "User is not a TA"},
    },
)

@router.patch(
    "/api/questions/{id}/resolve",
    tags=["Questions"],
    summary="Resolve a question",
    description="TA resolves a question with a resolution note. Works from both queued and in_progress status (TAs can resolve without claiming first).",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a TA"},
        404: {"model": ErrorResponse, "description": "Question not found"},
    },
)

@router.patch(
    "/api/questions/{id}/defer",
    tags=["Questions"],
    summary="Defer a question to back of queue",
    description="TA defers a question. Status is set to deferred, then immediately re-queued at the absolute back of the queue regardless of priority. Clears claimed_by and sets deferred_at.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a TA"},
        404: {"model": ErrorResponse, "description": "Question not found"},
    },
)

@router.patch(
    "/api/questions/{id}/withdraw",
    tags=["Questions"],
    summary="Withdraw a question",
    description="Student withdraws their own question. Only allowed when status is queued or in_progress. Cannot withdraw a resolved or already-withdrawn question.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Question is not in queued or in_progress status"},
        403: {"model": ErrorResponse, "description": "User is not the question owner"},
    },
)

@router.post(
    "/api/questions/{id}/helpful",
    tags=["Questions"],
    summary="Vote a question as helpful",
    description="Student votes a resolved question as helpful. One vote per student per question. Duplicate votes return 400.",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Already voted on this question"},
        403: {"model": ErrorResponse, "description": "User is not a student"},
    },
)
```

### Knowledge Base Routes (`routes/knowledge_base.py`)

```python
@router.get(
    "/api/knowledge-base",
    tags=["Knowledge Base"],
    summary="Search resolved questions",
    description="Search the knowledge base of resolved questions for a course. Supports keyword search and category filtering. Paginated at 20 results per page.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not enrolled in this course"},
    },
)

@router.get(
    "/api/knowledge-base/similar",
    tags=["Knowledge Base"],
    summary="Find similar resolved questions",
    description="Returns the top 5 resolved questions similar to the given title, matched by keyword. Used to show the 'Similar Questions' panel when a student is typing their question title.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a student in this course"},
    },
)
```

### Analytics Routes (`routes/analytics.py`)

```python
@router.get(
    "/api/analytics/overview",
    tags=["Analytics"],
    summary="Get analytics overview",
    description="Professor-only. Returns total questions, average wait time, average resolve time, and recent session summaries for a course.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a professor"},
    },
)

@router.get(
    "/api/analytics/categories",
    tags=["Analytics"],
    summary="Get category breakdown",
    description="Professor-only. Returns the distribution of questions across categories (debugging, conceptual, setup, assignment, other) with counts and percentages.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a professor"},
    },
)

@router.get(
    "/api/analytics/trends",
    tags=["Analytics"],
    summary="Get weekly question trends",
    description="Professor-only. Returns question volume per week for the last 8 weeks.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a professor"},
    },
)

@router.get(
    "/api/analytics/ta-performance",
    tags=["Analytics"],
    summary="Get TA performance metrics",
    description="Professor-only. Returns per-TA stats: resolved count, average resolve time, and rating.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User is not a professor"},
    },
)

@router.get(
    "/api/analytics/export",
    tags=["Analytics"],
    summary="Export analytics as CSV",
    description="Professor-only. Downloads a CSV file with analytics data for the course. Returns a file response, not JSON.",
    responses={
        403: {"model": ErrorResponse, "description": "User is not a professor"},
    },
)
```

### Notification Routes (`routes/notifications.py`)

```python
@router.get(
    "/api/notifications",
    tags=["Notifications"],
    summary="Get user notifications",
    description="Returns all notifications for the authenticated user, sorted newest first.",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)

@router.get(
    "/api/notifications/unread-count",
    tags=["Notifications"],
    summary="Get unread notification count",
    description="Returns the count of unread notifications for the authenticated user.",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)

@router.patch(
    "/api/notifications/{id}/read",
    tags=["Notifications"],
    summary="Mark a notification as read",
    description="Marks a single notification as read. User must own the notification.",
    response_model=SuccessResponse,
    responses={
        403: {"model": ErrorResponse, "description": "User does not own this notification"},
        404: {"model": ErrorResponse, "description": "Notification not found"},
    },
)

@router.patch(
    "/api/notifications/read-all",
    tags=["Notifications"],
    summary="Mark all notifications as read",
    description="Marks all of the authenticated user's notifications as read.",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
```

---

## TASK 4: Add Query Parameter Descriptions

**Files to modify:** Route files that accept query parameters.

**What to do:** Use FastAPI's `Query()` with descriptions for all query parameters.

```python
from fastapi import Query

# In sessions route
@router.get("/api/sessions")
async def list_sessions(
    course_id: UUID = Query(description="Filter sessions by course ID"),
    ...
):

# In questions route
@router.get("/api/questions")
async def list_questions(
    session_id: UUID = Query(description="Filter questions by session ID"),
    ...
):

# In knowledge base route
@router.get("/api/knowledge-base")
async def search_knowledge_base(
    course_id: UUID = Query(description="Course to search within"),
    search: Optional[str] = Query(None, description="Keyword search term"),
    category: Optional[QuestionCategory] = Query(None, description="Filter by question category"),
    page: int = Query(1, ge=1, description="Page number for pagination, starting at 1"),
    ...
):

@router.get("/api/knowledge-base/similar")
async def get_similar_questions(
    title: str = Query(description="Question title to find similar matches for"),
    course_id: UUID = Query(description="Course to search within"),
    ...
):

# In analytics routes
@router.get("/api/analytics/overview")
async def get_overview(
    course_id: UUID = Query(description="Course ID to get analytics for"),
    ...
):
# (same pattern for categories, trends, ta-performance, export)
```

---

## TASK 5: Verify the JWT Security Scheme

**File to check:** `server/app/core/deps.py` (or wherever `get_current_user` is defined).

**What to do:** Make sure the auth dependency uses `HTTPBearer` so Swagger UI shows the "Authorize" button with a lock icon.

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    # existing JWT validation logic stays the same
    ...
```

If it currently uses a different method (like reading headers manually), refactor it to use `HTTPBearer`. This is the only way FastAPI auto-generates the security scheme in OpenAPI.

---

## TASK 6: Final Verification

Run the server and verify at `http://localhost:8000/docs`:

1. Title shows "OfficeHoursQ API" with the full description
2. Seven tag groups appear in the sidebar: Auth, Courses, Sessions, Questions, Knowledge Base, Analytics, Notifications
3. All 28 endpoints appear under the correct tags
4. Every endpoint shows its summary, description, request body schema (with field descriptions), response schema, and error codes
5. The "Authorize" button appears at the top and accepts a Bearer JWT token
6. Clicking "Try it out" on any endpoint shows the correct request format
7. Enums (UserRole, QuestionCategory, QuestionPriority, etc.) render as dropdowns

Also verify `http://localhost:8000/redoc` loads correctly as an alternative view.

---

## THINGS TO NOT DO

- Do NOT create any `.md` files
- Do NOT create a separate OpenAPI spec file (`.yaml` or `.json`)
- Do NOT install any new documentation packages
- Do NOT change any business logic, database queries, or function bodies
- Do NOT rewrite route handler functions; only modify their decorators
- Do NOT remove any existing functionality
