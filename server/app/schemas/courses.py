from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
        description="Course name, e.g. 'CS5340 - HCI'",
    )


class CourseResponse(BaseModel):
    id: UUID = Field(description="Course ID")
    name: str = Field(description="Course name")
    invite_code: str = Field(
        description="6-char invite code for joining",
    )
    professor_id: UUID = Field(
        description="ID of the professor who owns the course",
    )
    created_at: datetime = Field(description="Creation timestamp")


class CourseJoin(BaseModel):
    invite_code: str = Field(
        min_length=6,
        max_length=6,
        description="6-character alphanumeric invite code",
    )


class CourseEnrollmentResponse(BaseModel):
    id: UUID = Field(description="Enrollment ID")
    course_id: UUID = Field(description="Enrolled course ID")
    user_id: UUID = Field(description="Enrolled user ID")
    role: str = Field(description="User role within the course")
    joined_at: datetime = Field(description="When the user joined the course")
