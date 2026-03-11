from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class KnowledgeBaseItem(BaseModel):
    id: str
    title: str
    description: str
    category: str
    resolution_note: Optional[str] = None
    helpful_votes: int = 0
    resolved_at: Optional[datetime] = None
    created_at: datetime
    student_name: Optional[str] = None


class SimilarQuestionItem(BaseModel):
    id: str
    title: str
    description: str
    category: str
    resolution_note: Optional[str] = None
    helpful_votes: int = 0
    resolved_at: Optional[datetime] = None
    created_at: datetime
    student_name: Optional[str] = None
    rank: Optional[float] = None
