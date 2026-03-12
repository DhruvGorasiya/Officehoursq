from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import QuestionCategory, QuestionPriority, QuestionStatus


class QuestionCreate(BaseModel):
    session_id: UUID = Field(description="ID of the active session to submit to")
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Brief summary of the issue",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Detailed problem description",
    )
    code_snippet: Optional[str] = Field(
        None,
        max_length=5000,
        description="Relevant code, optional",
    )
    error_message: Optional[str] = Field(
        None,
        max_length=1000,
        description="Error output, optional",
    )
    what_tried: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="What the student has already attempted",
    )
    category: QuestionCategory = Field(description="Question category")
    priority: QuestionPriority = Field(
        default=QuestionPriority.low,
        description="Self-assessed priority",
    )


class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Updated title",
    )
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=2000,
        description="Updated description",
    )
    code_snippet: Optional[str] = Field(
        None,
        max_length=5000,
        description="Updated code snippet",
    )
    error_message: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated error message",
    )
    what_tried: Optional[str] = Field(
        None,
        min_length=1,
        max_length=2000,
        description="Updated troubleshooting notes",
    )
    category: Optional[QuestionCategory] = Field(
        None,
        description="Updated category",
    )
    priority: Optional[QuestionPriority] = Field(
        None,
        description="Updated priority",
    )


class QuestionResolve(BaseModel):
    resolution_note: str = Field(
        ...,
        max_length=2000,
        description="How the question was resolved",
    )


class QuestionResponse(BaseModel):
    id: UUID = Field(description="Question ID")
    session_id: UUID = Field(
        description="Session this question belongs to",
    )
    course_id: UUID = Field(
        description="Course this question belongs to",
    )
    student_id: UUID = Field(
        description="ID of the student who submitted",
    )
    title: str = Field(description="Question title")
    description: str = Field(description="Full description")
    code_snippet: Optional[str] = Field(
        None,
        description="Code snippet if provided",
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if provided",
    )
    what_tried: str = Field(description="What the student tried")
    category: QuestionCategory = Field(description="Question category")
    priority: QuestionPriority = Field(description="Question priority")
    status: QuestionStatus = Field(
        description="Current status in the queue lifecycle",
    )
    queue_position: int = Field(
        description="Current position in the active queue, or -1 if not queued",
    )
    estimated_wait_minutes: Optional[int] = Field(
        None,
        description="Estimated wait time in minutes, if available",
    )
    claimed_by: Optional[UUID] = Field(
        None,
        description="ID of the TA who claimed this, if any",
    )
    resolution_note: Optional[str] = Field(
        None,
        description="Resolution details, if resolved",
    )
    claimed_at: Optional[datetime] = Field(
        None,
        description="When the question was claimed by a TA",
    )
    deferred_at: Optional[datetime] = Field(
        None,
        description="When the question was last deferred",
    )
    resolved_at: Optional[datetime] = Field(
        None,
        description="When the question was resolved",
    )
    created_at: datetime = Field(
        description="When the question was created",
    )
