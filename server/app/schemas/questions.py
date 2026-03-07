from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class QuestionCreate(BaseModel):
    session_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    code_snippet: Optional[str] = Field(None, max_length=5000)
    error_message: Optional[str] = Field(None, max_length=1000)
    what_tried: str = Field(..., min_length=1, max_length=2000)
    category: str
    priority: str = Field(default="low")

class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    code_snippet: Optional[str] = Field(None, max_length=5000)
    error_message: Optional[str] = Field(None, max_length=1000)
    what_tried: Optional[str] = Field(None, min_length=1, max_length=2000)
    category: Optional[str] = None
    priority: Optional[str] = None

class QuestionResolve(BaseModel):
    resolution_note: Optional[str] = None

class QuestionResponse(BaseModel):
    id: str
    session_id: str
    student_id: str
    title: str
    description: str
    code_snippet: Optional[str] = None
    error_message: Optional[str] = None
    what_tried: str
    category: str
    priority: str
    status: str
    queue_position: int
    claimed_by: Optional[str] = None
    resolution_note: Optional[str] = None
    claimed_at: Optional[datetime] = None
    deferred_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
