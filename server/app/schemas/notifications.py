from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import NotificationType


class NotificationResponse(BaseModel):
    id: UUID = Field(description="Notification ID")
    user_id: UUID = Field(description="Recipient user ID")
    type: NotificationType = Field(description="Notification type")
    message: str = Field(description="Human-readable notification message")
    related_question_id: Optional[UUID] = Field(
        None,
        description="Related question, if applicable",
    )
    related_session_id: Optional[UUID] = Field(
        None,
        description="Related session, if applicable",
    )
    is_read: bool = Field(
        description="Whether the user has read this notification",
    )
    created_at: datetime = Field(
        description="When the notification was created",
    )


class UnreadCountResponse(BaseModel):
    count: int = Field(description="Number of unread notifications")

