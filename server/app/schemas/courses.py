from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class CourseResponse(BaseModel):
    id: str
    name: str
    invite_code: str
    professor_id: str
    created_at: datetime

class CourseJoin(BaseModel):
    invite_code: str = Field(min_length=6, max_length=6)

class CourseEnrollmentResponse(BaseModel):
    id: str
    course_id: str
    user_id: str
    role: str
    joined_at: datetime
