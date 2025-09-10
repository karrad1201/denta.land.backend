from pydantic import BaseModel, Field, field_validator
from datetime import datetime, time
from typing import Dict, Optional


class WorkHours(BaseModel):
    open: time = Field(..., description="Время открытия")
    close: time = Field(..., description="Время закрытия")
    break_start: Optional[time] = Field(None, description="Начало перерыва")
    break_end: Optional[time] = Field(None, description="Конец перерыва")

    @field_validator('close')
    @classmethod
    def validate_close_time(cls, v: time, values) -> time:
        if 'open' in values.data and v <= values.data['open']:
            raise ValueError("Время закрытия должно быть после времени открытия")
        return v

    @field_validator('break_end')
    @classmethod
    def validate_break_time(cls, v: Optional[time], values) -> Optional[time]:
        if v is not None and 'break_start' in values.data and values.data['break_start'] is not None:
            if v <= values.data['break_start']:
                raise ValueError("Конец перерыва должен быть после начала")
        return v


class Clinic(BaseModel):
    id: int = Field(..., gt=0, description="Уникальный идентификатор клиники")
    organization_id: int = Field(..., gt=0, description="ID организации-владельца")
    name: str = Field(..., min_length=2, max_length=100, description="Название клиники")
    location: str = Field(..., min_length=2, max_length=100, description="Город/регион")
    address: str = Field(..., min_length=5, max_length=200, description="Полный адрес")
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    is_active: bool = Field(default=True, description="Флаг активности клиники")
    work_hours: Dict[str, Optional[WorkHours]] = Field(
        default_factory=dict,
        description="График работы по дням недели (пн-вс)"
    )
    is_24_7: bool = Field(default=False, description="Работает круглосуточно без выходных")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Название клиники не может быть пустым")
        return v.strip()

    @field_validator('work_hours')
    @classmethod
    def validate_work_hours(cls, v: Dict[str, Optional[WorkHours]], values) -> Dict[str, Optional[WorkHours]]:
        if values.data.get('is_24_7') and any(v.values()):
            raise ValueError("Для круглосуточной клиники не нужно указывать часы работы")
        return v
