from pydantic import Field
from typing import List
from src.domain.entity.users.user import User
from src.infrastructure.repository.schemas.user_orm import Role


class Organization(User):
    role: Role = Role.ORGANIZATION
    clinics: List[int] = Field(default_factory=list)
    members: List[int] = Field(default_factory=list)
    locations: List[str] = Field(..., min_items=1)
