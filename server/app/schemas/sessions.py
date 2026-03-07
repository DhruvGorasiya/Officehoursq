from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import Optional, List

class SessionCreate(BaseModel):
    course_id: str
    title: str = Field(..., min_length=1, max_length=200)
    date: date
    start_time: time
    end_time: time
    ta_ids: Optional[List[str]] = []

class SessionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    ta_ids: Optional[List[str]] = None

class SessionStatusUpdate(BaseModel):
    status: str = Field(..., description="'scheduled', 'active', or 'ended'")

class SessionResponse(BaseModel):
    id: str
    course_id: str
    title: str
    date: date
    start_time: time
    end_time: time
    status: str
    created_at: datetime
