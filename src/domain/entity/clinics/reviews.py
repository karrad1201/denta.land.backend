from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional
from src.domain.entity.users.user import Role  # Импорт ролей пользователей
from enum import Enum


class ReviewTargetType(str, Enum):
    SPECIALIST = "specialist"
    ORGANIZATION = "organization"
    CLINIC = "clinic"


class Review(BaseModel):
    id: Optional[int] = None
    sender_id: int = Field(..., gt=0, description="ID пользователя, оставившего отзыв")
    order_id: int = Field(..., gt=0, description="ID связанного заказа")
    target_id: int = Field(..., gt=0, description="ID цели отзыва")
    target_type: ReviewTargetType = Field(..., description="Тип цели отзыва")
    text: str = Field(..., min_length=10, max_length=2000, description="Текст отзыва")
    rate: int = Field(..., ge=1, le=10, description="Оценка от 1 до 10")
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    response: Optional[str] = Field(None, description="Ответ на отзыв")

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Текст отзыва должен содержать минимум 10 символов")
        return v.strip()

    @field_validator('rate')
    @classmethod
    def validate_rate(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("Оценка должна быть от 1 до 10")
        return v
