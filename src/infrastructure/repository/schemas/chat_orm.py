from src.infrastructure.repository.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from src.infrastructure.repository.schemas.enums import (
    RoleEnum,
    AdminRolesEnum,
    ResponseStatusEnum,
    OrderStatusEnum,
    MessageTypeEnum
)


class ChatOrm(Base):
    __tablename__ = "chats"
    initiator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    chat_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    response_id = Column(Integer, ForeignKey('responses.response_id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("MessageOrm", back_populates="chat", cascade="all, delete-orphan")


class MessageType(str, Enum):
    TEXT = 'text'
    VOICE = 'voice'
    FILE = 'file'
    IMAGE = 'image'


class MessageOrm(Base):
    __tablename__ = "messages"
    message_id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.chat_id'), nullable=False)
    sender_id = Column(Integer, nullable=False)

    type = Column(
        MessageTypeEnum,
        nullable=False
    )

    sent_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    chat = relationship("ChatOrm", back_populates="messages")


    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': MessageType.TEXT.value
    }


class TextMessageOrm(MessageOrm):
    __tablename__ = "text_messages"
    message_id = Column(Integer, ForeignKey("messages.message_id"), primary_key=True)
    text = Column(String(2000), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': MessageType.TEXT.value,
        'inherit_condition': (message_id == MessageOrm.message_id)
    }


class VoiceMessageOrm(MessageOrm):
    __tablename__ = "voice_messages"
    message_id = Column(Integer, ForeignKey("messages.message_id"), primary_key=True)
    audio_url = Column(String(255), nullable=False)
    duration_sec = Column(Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': MessageType.VOICE.value,
        'inherit_condition': (message_id == MessageOrm.message_id)
    }


class FileMessageOrm(MessageOrm):
    __tablename__ = "file_messages"
    message_id = Column(Integer, ForeignKey("messages.message_id"), primary_key=True)
    file_url = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': MessageType.FILE.value,
        'inherit_condition': (message_id == MessageOrm.message_id)
    }


class ImageMessageOrm(MessageOrm):
    __tablename__ = "image_messages"
    message_id = Column(Integer, ForeignKey("messages.message_id"), primary_key=True)
    image_url = Column(String(255), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': MessageType.IMAGE.value,
        'inherit_condition': (message_id == MessageOrm.message_id)
    }