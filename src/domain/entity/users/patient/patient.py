from src.domain.entity.users.user import User
from src.infrastructure.repository.schemas.user_orm import Role
from pydantic import Field
from typing import Optional


class Patient(User):
    city: Optional[str] = Field(default=None)
    role: Role = Role.PATIENT