from datetime import date as DateType, time as TimeType, datetime as DateTimeType
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import SessionStatus


class SessionCreate(BaseModel):
    course_id: UUID = Field(
        description="ID of the course this session belongs to",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Session title, e.g. 'Midterm Review'",
    )
    date: DateType = Field(description="Session date")
    start_time: TimeType = Field(description="Start time")
    end_time: TimeType = Field(description="End time")
    ta_ids: Optional[List[UUID]] = Field(
        default=None,
        description="List of TA user IDs assigned to this session",
    )


class SessionUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Updated session title",
    )
    date: Optional[DateType] = Field(
        None,
        description="Updated session date",
    )
    start_time: Optional[TimeType] = Field(
        None,
        description="Updated start time",
    )
    end_time: Optional[TimeType] = Field(
        None,
        description="Updated end time",
    )
    ta_ids: Optional[List[UUID]] = Field(
        None,
        description="Updated TA assignments",
    )


class SessionStatusUpdate(BaseModel):
    status: SessionStatus = Field(
        description="New status. Valid transitions: scheduled->active, active->ended",
    )


class SessionResponse(BaseModel):
    id: UUID = Field(description="Session ID")
    course_id: UUID = Field(description="Parent course ID")
    title: str = Field(description="Session title")
    date: DateType = Field(description="Session date")
    start_time: TimeType = Field(description="Start time")
    end_time: TimeType = Field(description="End time")
    status: SessionStatus = Field(description="Current session status")
    created_at: DateTimeType = Field(description="Creation timestamp")
