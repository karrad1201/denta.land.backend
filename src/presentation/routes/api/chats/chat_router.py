# src/api/routers/chat_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Union, Literal

from src.domain.entity.users.user import User
from src.domain.entity.chats.chat_entity import (
    Chat,  # Используем основную модель Chat
    Message,
    TextMessage,
    VoiceMessage,
    FileMessage,
    ImageMessage,
    MessageType
)
from src.use_cases.repository.chats_usecases import ChatUseCase
from src.dependencies import get_current_user, get_chats_use_case
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["Chats"])


class TextMessageRequest(BaseModel):
    recipient_id: int
    text: str


class BaseMessageResponse(BaseModel):
    message_id: int
    chat_id: int
    sender_id: int
    type: MessageType
    sent_at: datetime
    is_read: bool


@router.post("/send-text", status_code=status.HTTP_201_CREATED)
async def send_text_message(
        message_data: TextMessageRequest,
        current_user: User = Depends(get_current_user),
        use_case: ChatUseCase = Depends(get_chats_use_case)
):
    updated_chat = await use_case.send_text_message_to_recipient(
        sender_id=current_user.id,
        recipient_id=message_data.recipient_id,
        text=message_data.text
    )
    if not updated_chat:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки сообщения"
        )
    return {"chat_id": updated_chat.chat_id}


@router.get("/chats", response_model=List[Chat])
async def get_chats(
        current_user: User = Depends(get_current_user),
        use_case: ChatUseCase = Depends(get_chats_use_case)
):
    chats = await use_case.get_chats(current_user.id)
    if not chats:
        return []

    return chats


@router.get("/{chat_id}", response_model=Chat)
async def get_chat(
        chat_id: int,
        current_user: User = Depends(get_current_user),
        use_case: ChatUseCase = Depends(get_chats_use_case)
):
    chat = await use_case.get_chat(chat_id)
    if not chat or current_user.id not in chat.participants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден или у вас нет доступа"
        )
    return chat
