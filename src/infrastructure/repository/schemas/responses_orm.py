from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from src.infrastructure.repository.database import Base
from src.domain.entity.users.user import Role
from sqlalchemy import Enum as SQLAlchemyEnum
from src.infrastructure.repository.schemas.enums import (
    RoleEnum,
    AdminRolesEnum,
    ResponseStatusEnum,
    OrderStatusEnum,
    MessageTypeEnum
)


class ResponseOrm(Base):
    __tablename__ = 'responses'

    response_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    responser_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(
        SQLAlchemyEnum(Role),
        nullable=False
    )
    text = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(
        ResponseStatusEnum,
        default='proposed',
        nullable=False
    )
    updated_at = Column(DateTime, onupdate=datetime.utcnow)