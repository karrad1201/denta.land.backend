from pydantic import BaseModel, Field
from src.domain.entity.users.user import Role
from datetime import datetime
from typing import List, Optional
from enum import Enum


class OrderStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderBase(BaseModel):
    creator_id: int = Field(..., gt=0, description="ID создателя заказа")
    creator_role: Role = Field(..., description="Роль создателя")
    service_type: str = Field(..., description="Тип услуги")
    description: str = Field(..., min_length=10, max_length=500, description="Описание заказа")
    specifications: List[str] = Field(..., min_items=1, description="Спецификации")
    preferred_date: datetime = Field(..., description="Предпочитаемая дата и время")
    responses_count: int = Field(0, ge=0, description="Количество откликов")
    status: OrderStatus = Field(OrderStatus.ACTIVE, description="Статус заказа")


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    id: int = Field(..., gt=0, description="ID заказа")
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    # Дополнительные поля для связей
    patient_id: Optional[int] = Field(None, description="ID пациента (если применимо)")
    specialist_id: Optional[int] = Field(None, description="ID специалиста (если применимо)")
    clinic_id: Optional[int] = Field(None, description="ID клиники (если применимо)")
