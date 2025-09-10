import logging
from typing import Dict, Optional, List
from datetime import datetime

from src.infrastructure.adapters.orm_entity_adapter import UserOrmEntityAdapter
from src.domain.interfaces.chats.chats_repository import IChatsRepository
from src.domain.entity.chats.chat_entity import TextMessage, Chat, Message


class ChatUseCase:
    def __init__(
            self,
            chats_repo: IChatsRepository,
            adapter: UserOrmEntityAdapter
    ):
        self._chat_repo = chats_repo
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    async def send_text_message_to_recipient(self, sender_id: int, recipient_id: int, text: str) -> Optional[Chat]:
        try:
            self._logger.info(f"UC: Starting message send from {sender_id} to {recipient_id}")

            self._logger.info(f"UC: Searching chat for participants: {sender_id} and {recipient_id}")
            chat = await self._chat_repo.get_chat_by_participants(sender_id, recipient_id)

            if chat:
                self._logger.info(f"UC: Found existing chat ID: {chat.chat_id}")
            else:
                self._logger.info("UC: Chat not found, creating new chat")
                chat = await self._chat_repo.create_chat([sender_id, recipient_id])

                if not chat:
                    self._logger.error("UC: Chat creation failed!")
                    return None

                self._logger.info(f"UC: Created new chat ID: {chat.chat_id}")

            self._logger.info(f"UC: Adding message to chat {chat.chat_id}")
            updated_chat = await self._chat_repo.add_text_message_to_chat(
                chat_id=chat.chat_id,
                sender_id=sender_id,
                text=text
            )

            if updated_chat:
                self._logger.info(f"UC: Message added successfully to chat {chat.chat_id}")
                return updated_chat

            self._logger.error(f"UC: Failed to add message to chat {chat.chat_id}")
            return None

        except Exception as e:
            self._logger.error(f"UC: CRITICAL ERROR in send_text_message_to_recipient: {e}", exc_info=True)
            return None

    async def get_chats(self, user_id: int) -> List[Chat]:
        try:
            chats = await self._chat_repo.get_user_chats(user_id)
            return chats
        except Exception as e:
            self._logger.error(f'Error getting chats: {e}')
            return []

    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        try:
            chat = await self._chat_repo.get_chat(chat_id)
            return chat
        except Exception as e:
            self._logger.error(f'Error getting chat: {e}')
            return None

    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        try:
            return await self._chat_repo.delete_message(chat_id, message_id)
        except Exception as e:
            self._logger.error(f'Error deleting message: {e}')
            return False

    async def get_messages(self, chat_id: int) -> List[Message]:
        try:
            messages = await self._chat_repo.get_messages(chat_id)
            return messages
        except Exception as e:
            self._logger.error(f'Error getting messages: {e}')
            return []

    async def get_unread_messages(self, user_id: int) -> List[Message]:
        try:
            messages = await self._chat_repo.get_unread_messages(user_id)
            return messages
        except Exception as e:
            self._logger.error(f'Error getting unread messages: {e}')
            return []

    async def get_last_message(self, chat_id: int) -> Optional[Message]:
        try:
            message = await self._chat_repo.get_last_message(chat_id)
            return message
        except Exception as e:
            self._logger.error(f'Error getting last message: {e}')
            return None

    async def read_message(self, chat_id: int, message_id: int) -> bool:
        try:
            return await self._chat_repo.read_message(chat_id, message_id)
        except Exception as e:
            self._logger.error(f'Error reading message: {e}')
            return False

    async def edit_message(self, message: Message) -> bool:
        try:
            return await self._chat_repo.edit_message(message)
        except Exception as e:
            self._logger.error(f'Error editing message: {e}')
            return False

    async def mark_all_as_read(self, chat_id: int, user_id: int) -> bool:
        try:
            await self._chat_repo.mark_all_as_read(chat_id, user_id)
            return True
        except Exception as e:
            self._logger.error(f'Error marking messages as read: {e}')
            return False

    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        try:
            return await self._chat_repo.get_message(message_id)
        except Exception as e:
            self._logger.error(f'Error getting message: {e}')
            return None

    async def get_message(self, message_id: int) -> Optional[Message]:
        try:
            return await self._chat_repo.get_message(message_id)
        except Exception as e:
            self._logger.error(f'Error getting message: {e}')
            return None