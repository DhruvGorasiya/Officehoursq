from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import QuestionCategory


class OverviewResponse(BaseModel):
    total_questions: int = Field(
        description="Total questions across all sessions",
    )
    avg_wait_minutes: Optional[float] = Field(
        None,
        description="Average wait time in minutes",
    )
    avg_resolve_minutes: Optional[float] = Field(
        None,
        description="Average resolution time in minutes",
    )
    recent_sessions: List[dict] = Field(
        description="List of recent session summaries",
    )


class CategoryBreakdown(BaseModel):
    category: QuestionCategory = Field(description="Question category")
    count: int = Field(description="Number of questions in this category")
    percentage: float = Field(
        description="Percentage of total resolved questions",
    )


class WeeklyTrend(BaseModel):
    week_start: str = Field(
        description="ISO date string for the Monday that starts this week",
    )
    count: int = Field(description="Number of questions that week")


class TAPerformance(BaseModel):
    id: UUID = Field(description="TA's user ID")
    name: str = Field(description="TA's display name")
    initials: str = Field(description="Derived initials for avatar display")
    resolved_count: int = Field(
        description="Total questions resolved by this TA",
    )
    avg_resolve_minutes: Optional[float] = Field(
        None,
        description="Average time to resolve in minutes",
    )
    rating: int = Field(
        description="Heuristic star rating derived from resolution time",
    )

