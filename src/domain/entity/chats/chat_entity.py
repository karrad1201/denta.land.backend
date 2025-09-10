from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, Union, Dict, Literal, List
from enum import Enum
from datetime import datetime


class MessageType(str, Enum):
    TEXT = 'text'
    VOICE = 'voice'
    FILE = 'file'
    IMAGE = 'image'


class MessageBase(BaseModel):
    chat_id: int = Field(..., gt=0, description="ID чата")
    sender_id: int = Field(..., gt=0, description="ID отправителя")
    type: MessageType = Field(..., description="Тип сообщения")
    sent_at: datetime = Field(default_factory=datetime.now, description="Время отправки")
    message_id: int = Field(..., gt=0, description="Уникальный ID сообщения")
    is_read: bool = Field(default=False, description="Флаг прочтения")


class TextMessage(MessageBase):
    # Используем Literal вместо const
    type: Literal[MessageType.TEXT] = Field(default=MessageType.TEXT, frozen=True)
    text: str = Field(..., min_length=1, max_length=2000, description="Текст сообщения")

    @field_validator('text')
    @classmethod
    def validate_text_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Текст сообщения не может быть пустым")
        return v


class VoiceMessage(MessageBase):
    type: Literal[MessageType.VOICE] = MessageType.VOICE
    audio_url: str = Field(..., pattern=r'^https?://', description="URL аудиофайла")
    duration_sec: float = Field(..., gt=0, le=300, description="Длительность (секунды)")


class FileMessage(MessageBase):
    type: Literal[MessageType.FILE] = MessageType.FILE
    file_url: str = Field(..., pattern=r'^https?://', description="URL файла")
    file_name: str = Field(..., min_length=1, description="Имя файла")
    file_size: int = Field(..., gt=0, description="Размер файла (байты)")


class ImageMessage(MessageBase):
    type: Literal[MessageType.IMAGE] = MessageType.IMAGE
    image_url: str = Field(..., pattern=r'^https?://', description="URL изображения")
    width: int = Field(..., gt=0, description="Ширина изображения")
    height: int = Field(..., gt=0, description="Высота изображения")


Message = Union[TextMessage, VoiceMessage, FileMessage, ImageMessage]

from pydantic import ConfigDict


class Chat(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    chat_id: int = Field(..., gt=0, description="Уникальный ID чата", alias='id')
    initiator_id: int = Field(..., gt=0)
    recipient_id: int = Field(..., gt=0)
    order_id: Optional[int] = Field(None, gt=0)
    response_id: Optional[int] = Field(None, gt=0)
    created_at: datetime = Field(default_factory=datetime.now)
    messages: List[Message] = Field(default_factory=list)

    @computed_field
    @property
    def participants(self) -> List[int]:
        return [self.initiator_id, self.recipient_id]


class InputData(BaseModel):
    message: Message

    @classmethod
    def from_dict(cls, data: Dict):
        return cls.model_validate(data)
