from pydantic import BaseModel
from typing import Any


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
