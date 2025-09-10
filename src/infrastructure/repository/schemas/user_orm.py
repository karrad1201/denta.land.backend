from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from src.infrastructure.repository.database import Base
from sqlalchemy import Enum as SQLAlchemyEnum
from pydantic import BaseModel
from src.infrastructure.repository.schemas.enums import (
    RoleEnum,
    AdminRolesEnum,
    ResponseStatusEnum,
    OrderStatusEnum,
    MessageTypeEnum
)


class Role(str, PyEnum):
    ORGANIZATION = 'organization'
    SPECIALIST = 'specialist'
    PATIENT = 'patient'
    ADMIN = 'admin'


class AdminRoles(str, PyEnum):
    HELPER = 'helper'
    MODERATOR = 'moderator'
    TECH_ADMIN = 'tech_admin'
    ADMINISTRATOR = 'administrator'


class UserOrm(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    nickname = Column(String(10), unique=True, nullable=False)
    name = Column(String(15), nullable=False)
    role = Column(
        SQLAlchemyEnum(Role),
        nullable=False
    )
    photo_path = Column(String, nullable=True)
    country = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    specialist = relationship("SpecialistOrm", uselist=False, back_populates="user")
    patient = relationship("PatientOrm", uselist=False, back_populates="user")
    organization = relationship("OrganizationOrm", uselist=False, back_populates="user")
    admin = relationship("AdminOrm", uselist=False, back_populates="user")
    blocked_user = relationship("BlockedUserOrm", uselist=False, back_populates="user")

    __mapper_args__ = {
        'polymorphic_on': 'role'
    }


class SpecialistOrm(Base):
    """ORM модель специалиста"""
    __tablename__ = 'specialists'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    specifications = Column(JSON, nullable=False)
    qualification = Column(String(100), nullable=True)
    experience_years = Column(Integer, default=0)

    user = relationship("UserOrm", back_populates="specialist")

    __mapper_args__ = {
        'polymorphic_identity': 'specialist'
    }


class PatientOrm(Base):
    """ORM модель пациента"""
    __tablename__ = 'patients'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    city = Column(String, nullable=False)

    user = relationship("UserOrm", back_populates="patient")

    __mapper_args__ = {
        'polymorphic_identity': 'patient'
    }


class OrganizationOrm(Base):
    """ORM модель организации"""
    __tablename__ = 'organizations'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    clinics = relationship("ClinicOrm", back_populates="organization")
    members = Column(JSON, default=list)
    locations = Column(JSON, nullable=False)

    user = relationship("UserOrm", back_populates="organization")

    __mapper_args__ = {
        'polymorphic_identity': 'organization'
    }


class AdminOrm(Base):
    __tablename__ = 'admins'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    admin_role = Column(
        SQLAlchemyEnum(AdminRoles),
        nullable=False
    )
    is_superadmin = Column(Boolean, default=False)

    user = relationship("UserOrm", back_populates="admin")

    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }


class BlockedUserOrm(Base):
    __tablename__ = 'blocked_users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    reason = Column(String, nullable=True)
    blocked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserOrm", back_populates="blocked_user")

    __mapper_args__ = {
        'polymorphic_identity': 'blocked_user'
    }


from typing import Optional


class AdminActionsSchema(BaseModel):
    action: str
    user_id: int
    reason: Optional[str] = None
