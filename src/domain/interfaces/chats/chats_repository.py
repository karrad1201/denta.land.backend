# src/domain/interfaces/chats/chats_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entity.chats.chat_entity import Chat, Message


class IChatsRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        """Получает чат по его ID."""
        pass

    @abstractmethod
    async def get_chat_by_participants(self, user_id: int, recipient_id: int) -> Optional[Chat]:
        """Находит чат, в котором участвуют два указанных пользователя."""
        pass

    @abstractmethod
    async def create_chat(self, participants: List[int]) -> Chat:
        """Создает новый чат с указанными участниками."""
        pass

    @abstractmethod
    async def add_message_to_chat(self, chat_id: int, message: Message) -> Optional[Chat]:
        """Добавляет сообщение в существующий чат."""
        pass

    @abstractmethod
    async def get_user_chats(self, user_id: int) -> List[Chat]:
        """Получает список чатов, в которых участвует пользователь."""
        pass

    @abstractmethod
    async def get_messages(self, chat_id: int) -> List[Message]:
        """Получает все сообщения в указанном чате."""
        pass

    @abstractmethod
    async def get_message(self, message_id: int) -> Optional[Message]:
        """Получает конкретное сообщение по его ID."""
        pass

    @abstractmethod
    async def read_message(self, chat_id: int, message_id: int) -> bool:
        """Помечает сообщение как прочитанное."""
        pass

    @abstractmethod
    async def mark_all_as_read(self, chat_id: int, user_id: int) -> bool:
        """Помечает все непрочитанные сообщения в чате как прочитанные."""
        pass

    @abstractmethod
    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        """Удаляет сообщение из чата."""
        pass

    @abstractmethod
    async def edit_message(self, message: Message) -> bool:
        """Редактирует существующее сообщение."""
        pass

    @abstractmethod
    async def get_last_message(self, chat_id: int) -> Optional[Message]:
        """Получает последнее сообщение в чате."""
        pass

    @abstractmethod
    async def get_unread_messages_count(self, chat_id: int, user_id: int) -> int:
        """Возвращает количество непрочитанных сообщений в чате для пользователя."""
        pass

    @abstractmethod
    async def add_text_message_to_chat(self, chat_id: int, sender_id: int, text: str):
        pass
