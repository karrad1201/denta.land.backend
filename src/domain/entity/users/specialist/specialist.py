from pydantic import Field
from typing import Optional, List
from src.domain.entity.users.user import User
from src.infrastructure.repository.schemas.user_orm import Role


class Specialist(User):
    role: Role = Role.SPECIALIST
    specifications: List[str] = Field(..., min_items=1)
    qualification: Optional[str] = Field(None, max_length=100)
    experience_years: int = Field(0, ge=0)
