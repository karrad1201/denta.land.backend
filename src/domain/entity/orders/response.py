from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class Role(str, Enum):
    PATIENT = "patient"
    SPECIALIST = "specialist"
    ORGANIZATION = "organization"
    ADMIN = "admin"


class ResponseStatus(str, Enum):
    PROPOSED = "proposed"
    DENIED = "denied"
    TAKEN = "taken"
    COMPLETED = "completed"
    PREMATURELY_CLOSED = "prematurely_closed"


class ResponseCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    responser_id: int = Field(..., gt=0)
    role: Role
    text: str = Field(..., min_length=10, max_length=1000)


class Response(ResponseCreate):
    response_id: int = Field(..., gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: ResponseStatus = Field(default=ResponseStatus.PROPOSED)
    updated_at: Optional[datetime] = None
