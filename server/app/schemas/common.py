from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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


class SuccessResponse(BaseModel):
    success: bool = Field(
        default=True, description="Always true for successful responses"
    )
    data: Any = Field(description="Response payload")


class ErrorResponse(BaseModel):
    success: bool = Field(
        default=False, description="Always false for error responses"
    )
    message: str = Field(description="Human-readable error message")


class PaginatedSuccessResponse(SuccessResponse):
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_count: int = Field(description="Total number of items across all pages")
