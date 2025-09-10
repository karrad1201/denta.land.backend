from abc import ABC, abstractmethod
from src.domain.entity.users.user import UserInput, User, UserFull
from typing import Optional, ClassVar
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from src.infrastructure.repository.schemas.user_orm import Role


class SettingsUserData(BaseModel):
    nickname: str = Field(..., pattern='^[a-zA-Z0-9_]+$', min_length=4, max_length=20)
    name: str = Field(..., min_length=2, max_length=30)
    role: Role
    photo_path: Optional[str] = None
    country: str
    email: str
    password: str = Field(..., min_length=8, max_length=30)

    # Исправленные поля с аннотацией типов
    password_hash: ClassVar[None] = None
    id: int
    created_at: ClassVar[None] = None


class IUserRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def create(self, user: UserInput) -> str | Exception:
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_nickname(self, nickname: str) -> Optional[User]:
        pass

    @abstractmethod
    async def update(self, user_id: int, update_data: dict) -> bool:
        pass

    @abstractmethod
    async def _verify_password(self, password: str, hashed_password: str) -> bool:
        pass

    @abstractmethod
    async def _generate_jwt_token(self, user_id: int) -> str:
        pass

    @abstractmethod
    async def _decode_jwt_token(self, token: str) -> int:
        pass

    @abstractmethod
    async def get_password_hash(self, nickname: str) -> str:
        pass

    @abstractmethod
    async def delete(self, user: UserFull) -> bool:
        pass

    @abstractmethod
    async def check_register(self, nickname: str, password: str) -> str:  # JWT
        pass

    @abstractmethod
    async def set_settings(self, user: SettingsUserData) -> bool:
        pass

    @abstractmethod
    async def check_nickname_exists(self, nickname: str) -> bool:
        pass

    @abstractmethod
    async def check_email_exists(self, mail: str) -> bool:
        pass
