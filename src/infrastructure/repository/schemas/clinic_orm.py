from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from src.infrastructure.repository.database import Base
from src.infrastructure.repository.schemas.enums import (
    RoleEnum,
    AdminRolesEnum,
    ResponseStatusEnum,
    OrderStatusEnum,
    MessageTypeEnum
)



class ClinicOrm(Base):
    __tablename__ = 'clinics'
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.user_id'))
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    work_hours = Column(JSON, nullable=False)
    is_24_7 = Column(Boolean, default=False, nullable=False)

    # Отношение к организации
    organization = relationship("OrganizationOrm", back_populates="clinics")
