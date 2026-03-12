from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import QuestionCategory


class KnowledgeBaseItem(BaseModel):
    id: UUID = Field(description="Question ID")
    title: str = Field(description="Question title")
    description: str = Field(description="Full question description")
    category: QuestionCategory = Field(description="Question category")
    resolution_note: Optional[str] = Field(
        None,
        description="How the question was resolved, if available",
    )
    helpful_votes: int = Field(
        default=0,
        description="Number of helpful votes",
    )
    resolved_at: Optional[datetime] = Field(
        None,
        description="When the question was resolved",
    )
    created_at: datetime = Field(
        description="When the question was originally created",
    )
    student_name: Optional[str] = Field(
        None,
        description="Display name of the student who asked the question",
    )


class SimilarQuestionItem(BaseModel):
    id: UUID = Field(description="Question ID")
    title: str = Field(description="Question title")
    description: str = Field(description="Full question description")
    category: QuestionCategory = Field(description="Question category")
    resolution_note: Optional[str] = Field(
        None,
        description="How the question was resolved, if available",
    )
    helpful_votes: int = Field(
        default=0,
        description="Number of helpful votes",
    )
    resolved_at: Optional[datetime] = Field(
        None,
        description="When the question was resolved",
    )
    created_at: datetime = Field(
        description="When the question was originally created",
    )
    student_name: Optional[str] = Field(
        None,
        description="Display name of the student who asked the question",
    )
    rank: Optional[float] = Field(
        None,
        description="Similarity rank score from the database function",
    )
