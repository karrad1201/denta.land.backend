from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from src.infrastructure.repository.database import Base
from src.domain.entity.clinics.reviews import ReviewTargetType


class ReviewOrm(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    target_id = Column(Integer, nullable=False)
    target_type = Column(Enum(ReviewTargetType), nullable=False)
    text = Column(String(2000), nullable=False)
    rate = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    response = Column(String(2000), nullable=True)

    sender = relationship("UserOrm", foreign_keys=[sender_id])
    order = relationship("OrderOrm", foreign_keys=[order_id])

    __table_args__ = (
        CheckConstraint('rate >= 1 AND rate <= 10', name='ck_review_rate_range'),
    )
