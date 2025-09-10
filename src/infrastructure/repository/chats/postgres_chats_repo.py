import logging
from typing import List, Optional
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.adapters.orm_entity_adapter import ChatOrmEntityAdapter, MessageOrmEntityAdapter
from src.domain.interfaces.chats.chats_repository import IChatsRepository
from src.infrastructure.repository.schemas.chat_orm import ChatOrm, MessageOrm, TextMessageOrm, VoiceMessageOrm, \
    ImageMessageOrm, FileMessageOrm
from src.domain.entity.chats.chat_entity import Chat, Message, TextMessage
from sqlalchemy.orm import with_polymorphic
from datetime import datetime


class PostgresChatsRepo(IChatsRepository):
    def __init__(self, session: AsyncSession, Chat_adapter: ChatOrmEntityAdapter,
                 message_adapter: MessageOrmEntityAdapter):
        self._session = session
        self._chat_adapter = Chat_adapter
        self._message_adapter = message_adapter
        self._logger = logging.getLogger(__name__)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        try:
            msg_poly = with_polymorphic(
                MessageOrm,
                [TextMessageOrm, VoiceMessageOrm, FileMessageOrm, ImageMessageOrm]
            )
            stmt = (
                select(ChatOrm)
                .where(ChatOrm.chat_id == chat_id)
                .options(selectinload(ChatOrm.messages.of_type(msg_poly)))
            )
            result = await self._session.execute(stmt)
            chat_orm = result.scalar_one_or_none()
            return await self._chat_adapter.to_entity(chat_orm) if chat_orm else None
        except Exception as e:
            self._logger.error(f"Error getting chat by ID {chat_id}: {e}", exc_info=True)
            return None

    async def get_chat_by_participants(self, user_id: int, recipient_id: int) -> Optional[Chat]:
        try:
            msg_poly = with_polymorphic(
                MessageOrm,
                [TextMessageOrm, VoiceMessageOrm, FileMessageOrm, ImageMessageOrm]
            )
            stmt = (
                select(ChatOrm)
                .filter(
                    or_(
                        and_(ChatOrm.initiator_id == user_id, ChatOrm.recipient_id == recipient_id),
                        and_(ChatOrm.initiator_id == recipient_id, ChatOrm.recipient_id == user_id)
                    )
                )
                .options(selectinload(ChatOrm.messages.of_type(msg_poly)))
            )
            result = await self._session.execute(stmt)
            chat_orm = result.scalar_one_or_none()

            if chat_orm:
                return await self._chat_adapter.to_entity(chat_orm)
            return None
        except Exception as e:
            self._logger.error(f"Error getting chat by participants: {e}", exc_info=True)
            return None

    async def create_chat(self, participants: List[int]) -> Optional[Chat]:
        try:
            if len(participants) != 2:
                raise ValueError("Chat must have exactly 2 participants")

            chat_orm = ChatOrm(
                initiator_id=participants[0],
                recipient_id=participants[1]
            )
            self._session.add(chat_orm)
            await self._session.commit()
            await self._session.refresh(chat_orm)

            return await self.get_chat(chat_orm.chat_id)
        except Exception as e:
            self._logger.error(f"Error creating chat: {e}", exc_info=True)
            await self._session.rollback()
            return None

    async def add_message_to_chat(self, chat_id: int, message: Message) -> Optional[Chat]:
        try:
            self._logger.info(f"REPO: Adding message to chat {chat_id}")
            self._logger.debug(f"Message details: {message}")

            self._logger.info("Converting message to ORM")
            message_orm = await self._message_adapter.to_orm(message)
            self._logger.debug(f"Converted ORM: {message_orm}")

            message_orm.chat_id = chat_id
            self._logger.info(f"Set chat_id: {chat_id} for message")

            self._session.add(message_orm)
            self._logger.info("Message added to session")

            await self._session.commit()
            self._logger.info("Commit successful")

            await self._session.refresh(message_orm)
            self._logger.info(f"Message refreshed: {message_orm}")

            # Получаем обновленный чат для возврата
            self._logger.info(f"Retrieving updated chat {chat_id}")
            updated_chat = await self.get_chat(chat_id)

            if updated_chat:
                self._logger.info(f"Chat retrieved successfully: {updated_chat}")
            else:
                self._logger.warning("Chat not found after update")

            return updated_chat

        except Exception as e:
            self._logger.error(f"REPO: ERROR adding message to chat {chat_id}: {e}", exc_info=True)
            await self._session.rollback()
            return None

    async def get_user_chats(self, user_id: int) -> List[Chat]:
        try:
            # Используем with_polymorphic для загрузки всех типов сообщений
            msg_poly = with_polymorphic(
                MessageOrm,
                [TextMessageOrm, VoiceMessageOrm, FileMessageOrm, ImageMessageOrm]
            )

            # Создаем корректный запрос с join для загрузки сообщений
            stmt = (
                select(ChatOrm)
                .where(or_(
                    ChatOrm.initiator_id == user_id,
                    ChatOrm.recipient_id == user_id
                ))
                .options(selectinload(ChatOrm.messages.of_type(msg_poly)))
                .order_by(ChatOrm.created_at.desc())  # Сортировка по дате создания
            )

            result = await self._session.execute(stmt)
            chat_orms = result.scalars().all()

            if not chat_orms:
                return []

            # Конвертируем ORM-объекты в сущности
            return [await self._chat_adapter.to_entity(chat) for chat in chat_orms]
        except Exception as e:
            self._logger.error(f"Error getting chats for user {user_id}: {e}", exc_info=True)
            return []

    async def get_messages(self, chat_id: int) -> List[Message]:
        try:
            msg_poly = with_polymorphic(
                MessageOrm,
                [TextMessageOrm, VoiceMessageOrm, FileMessageOrm, ImageMessageOrm]
            )
            stmt = select(msg_poly).where(MessageOrm.chat_id == chat_id)
            result = await self._session.execute(stmt)
            messages_orm = result.scalars().all()
            return [await self._message_adapter.to_entity(msg) for msg in messages_orm]
        except Exception as e:
            self._logger.error(f"Error getting messages for chat {chat_id}: {e}", exc_info=True)
            return []

    async def get_message(self, message_id: int) -> Optional[Message]:
        try:
            msg_poly = with_polymorphic(
                MessageOrm,
                [TextMessageOrm, VoiceMessageOrm, FileMessageOrm, ImageMessageOrm]
            )
            stmt = select(msg_poly).where(MessageOrm.message_id == message_id)
            result = await self._session.execute(stmt)
            message_orm = result.scalar_one_or_none()
            return await self._message_adapter.to_entity(message_orm) if message_orm else None
        except Exception as e:
            self._logger.error(f"Error getting message by ID {message_id}: {e}", exc_info=True)
            return None

    async def read_message(self, chat_id: int, message_id: int) -> bool:
        try:
            message = await self._session.get(MessageOrm, message_id)
            if message:
                message.is_read = True
                await self._session.commit()
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error reading message {message_id} in chat {chat_id}: {e}", exc_info=True)
            await self._session.rollback()
            return False

    async def mark_all_as_read(self, chat_id: int, user_id: int) -> bool:
        try:
            stmt = select(MessageOrm).where(MessageOrm.chat_id == chat_id, MessageOrm.sender_id != user_id,
                                            MessageOrm.is_read == False)
            result = await self._session.execute(stmt)
            messages = result.scalars().all()
            for message in messages:
                message.is_read = True
            await self._session.commit()
            return True
        except Exception as e:
            self._logger.error(f"Error marking messages as read in chat {chat_id} for user {user_id}: {e}",
                               exc_info=True)
            await self._session.rollback()
            return False

    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        try:
            message_orm = await self._session.get(MessageOrm, message_id)
            if message_orm:
                await self._session.delete(message_orm)
                await self._session.commit()
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error deleting message {message_id}: {e}", exc_info=True)
            await self._session.rollback()
            return False

    async def edit_message(self, message: Message) -> bool:
        try:
            message_orm = await self._session.get(MessageOrm, message.id)
            if message_orm:
                if isinstance(message, TextMessage):
                    message_orm.text = message.text
                await self._session.commit()
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error editing message {message.id}: {e}", exc_info=True)
            await self._session.rollback()
            return False

    async def get_last_message(self, chat_id: int) -> Optional[Message]:
        try:
            msg_poly = with_polymorphic(
                MessageOrm,
                [TextMessageOrm, VoiceMessageOrm, FileMessageOrm, ImageMessageOrm]
            )
            stmt = (
                select(msg_poly)
                .where(MessageOrm.chat_id == chat_id)
                .order_by(MessageOrm.sent_at.desc())
            )
            result = await self._session.execute(stmt)
            message_orm = result.scalars().first()
            return await self._message_adapter.to_entity(message_orm) if message_orm else None
        except Exception as e:
            self._logger.error(f"Error getting last message for chat {chat_id}: {e}", exc_info=True)
            return None

    async def get_unread_messages_count(self, chat_id: int, user_id: int) -> int:
        try:
            stmt = select(func.count(MessageOrm.id)).where(
                MessageOrm.chat_id == chat_id,
                MessageOrm.sender_id != user_id,
                MessageOrm.is_read == False
            )
            result = await self._session.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            self._logger.error(f"Error getting unread messages count for chat {chat_id} and user {user_id}: {e}",
                               exc_info=True)
            return 0

    async def add_text_message_to_chat(self, chat_id: int, sender_id: int, text: str) -> Optional[Chat]:
        """
        Создает и добавляет текстовое сообщение в чат.
        """
        try:
            self._logger.info(f"REPO: Adding text message to chat {chat_id}")
            text_message_orm = TextMessageOrm(
                chat_id=chat_id,
                sender_id=sender_id,
                text=text,
                sent_at=datetime.utcnow()
            )

            self._session.add(text_message_orm)
            await self._session.commit()
            await self._session.refresh(text_message_orm)

            # Получаем обновленный чат с новым сообщением для возврата
            self._logger.info(f"Retrieving updated chat {chat_id}")
            updated_chat = await self.get_chat(chat_id)

            if updated_chat:
                self._logger.info(f"Chat retrieved successfully: {updated_chat}")
            else:
                self._logger.warning("Chat not found after update")

            return updated_chat

        except Exception as e:
            self._logger.error(f"REPO: ERROR adding text message to chat {chat_id}: {e}", exc_info=True)
            await self._session.rollback()
            return None
