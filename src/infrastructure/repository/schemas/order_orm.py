from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from datetime import datetime
from src.infrastructure.repository.database import Base
from sqlalchemy import Enum as SQLAlchemyEnum
from enum import Enum


class OrderStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderCreatorRole(str, Enum):
    PATIENT = "patient"
    SPECIALIST = "specialist"
    ORGANIZATION = "organization"


class OrderOrm(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey('users.id'))
    creator_role = Column(SQLAlchemyEnum(OrderCreatorRole))
    service_type = Column(String(50))
    description = Column(String(500))
    specifications = Column(JSON, nullable=False, default=[])
    preferred_date = Column(DateTime)
    responses_count = Column(Integer, default=0)
    status = Column(SQLAlchemyEnum(OrderStatus), default=OrderStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    # Дополнительные связи
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    specialist_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=True)
