from src.infrastructure.repository.schemas.user_orm import Role
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Union



class UserBase(BaseModel):
    id: Optional[int] = None
    nickname: str = Field(..., pattern='^[a-zA-Z0-9_]+$', min_length=4, max_length=20)
    name: str = Field(..., min_length=2, max_length=30)
    role: Role
    photo_path: Optional[str] = None
    country: str
    email: str
    phone_number: str = Field(..., min_length=5, max_length=20)


class User(UserBase):
    pass


class UserInput(UserBase):
    password: str = ""
    password_hash: str = ""
    id: Optional[int] = None


class UserPrivate(UserInput):
    mail: str
    password_hash: str = ""


class UserFull(UserPrivate):
    created_at: datetime
