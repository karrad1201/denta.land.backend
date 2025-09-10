import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.declarative import DeclarativeMeta

from src.domain.entity.chats.chat_entity import Chat, Message, MessageType, VoiceMessage, TextMessage, FileMessage, \
    ImageMessage
from src.domain.entity.clinics.clinic_entity import Clinic, WorkHours
from src.domain.entity.clinics.reviews import Review, ReviewTargetType
from src.domain.entity.orders.order import Order, OrderStatus
from src.domain.entity.orders.response import Response, ResponseStatus, ResponseCreate
from src.infrastructure.repository.schemas.enums import ResponseStatusEnum
from src.domain.entity.users.admin.admin_entity import Admin, AdminRoles
from src.domain.entity.users.organization.organization import Organization
from src.domain.entity.users.patient.patient import Patient
from src.domain.entity.users.specialist.specialist import Specialist
from src.domain.entity.users.user import User, Role
from src.infrastructure.repository.schemas.chat_orm import ChatOrm, MessageOrm, TextMessageOrm, VoiceMessageOrm, \
    FileMessageOrm, ImageMessageOrm
from src.infrastructure.repository.schemas.clinic_orm import ClinicOrm
from src.infrastructure.repository.schemas.order_orm import OrderOrm, OrderCreatorRole
from src.infrastructure.repository.schemas.responses_orm import ResponseOrm
from src.infrastructure.repository.schemas.review_orm import ReviewOrm
from src.infrastructure.repository.schemas.user_orm import UserOrm, SpecialistOrm, AdminOrm, PatientOrm, \
    OrganizationOrm, BlockedUserOrm, RoleEnum
from enum import Enum
from typing import Union
from datetime import datetime

T_ORM = TypeVar('T_ORM', bound=DeclarativeMeta)
T_Entity = TypeVar('T_Entity', bound=BaseModel)


class UserOrmEntityAdapter:
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    async def to_entity(self, orm_entity):
        """Преобразует ORM-объект в сущность (Entity)"""
        try:
            user_orm = orm_entity.user if hasattr(orm_entity, 'user') else orm_entity

            base_data = {
                'id': user_orm.id,
                'nickname': user_orm.nickname,
                'name': user_orm.name,
                'role': user_orm.role,
                'photo_path': user_orm.photo_path,
                'country': user_orm.country,
                'email': user_orm.email,
                'phone_number': user_orm.phone_number,
                'created_at': user_orm.created_at,
                'is_active': user_orm.blocked_user is None,
                'blocked_reason': getattr(user_orm.blocked_user, 'reason', None)
            }

            profile_data = {}
            entity_class = User

            if user_orm.role == Role.PATIENT.value and user_orm.patient:
                entity_class = Patient
                profile_data = {
                    'city': getattr(user_orm.patient, 'city', None),
                }
            elif user_orm.role == Role.SPECIALIST.value and user_orm.specialist:
                entity_class = Specialist
                profile_data = {
                    'experience_years': getattr(user_orm.specialist, 'experience_years', 0),
                    'specifications': getattr(user_orm.specialist, 'specifications', []),
                    'is_verified': getattr(user_orm.specialist, 'is_verified', False),
                    'qualification': getattr(user_orm.specialist, 'qualification', None),
                    'is_active': getattr(user_orm.specialist, 'is_active', False),
                    'appointments': getattr(user_orm.specialist, 'appointments', []),
                }
            elif user_orm.role == Role.ORGANIZATION.value and user_orm.organization:
                entity_class = Organization
                clinics = [clinic.id for clinic in getattr(user_orm.organization, 'clinics', [])]
                profile_data = {
                    'legal_name': getattr(user_orm.organization, 'legal_name', None),
                    'locations': getattr(user_orm.organization, 'locations', []),
                    'clinics': clinics,
                    'appointments': getattr(user_orm.organization, 'appointments', []),
                }
            elif user_orm.role == Role.ADMIN.value and user_orm.admin:
                entity_class = Admin
                profile_data = {
                    'admin_role': getattr(user_orm.admin, 'admin_role', None),
                    'is_superadmin': getattr(user_orm.admin, 'is_superadmin', False),
                }

            return entity_class(**{**base_data, **profile_data})

        except ValidationError as e:
            self._logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self._logger.error(f"ORM to Entity error: {e}", exc_info=True)
            raise

    async def to_orm(self, user_entity: User) -> UserOrm:
        try:
            base_data = {
                'nickname': user_entity.nickname,
                'name': user_entity.name,
                'role': Role(user_entity.role),
                'photo_path': user_entity.photo_path,
                'country': user_entity.country,
                'email': user_entity.email,
                'phone_number': user_entity.phone_number,
                'password_hash': user_entity.password_hash
            }

            if user_entity.id:
                base_data['id'] = user_entity.id

            user_orm = UserOrm(**base_data)

            # Создаем связанные объекты ТОЛЬКО если есть соответствующие данные
            if user_entity.role == Role.SPECIALIST and hasattr(user_entity, 'specifications'):
                specialist = SpecialistOrm(
                    user_id=user_entity.id,
                    specifications=user_entity.specifications,
                    qualification=getattr(user_entity, 'qualification', None),
                    experience_years=user_entity.experience_years
                )
                user_orm.specialist = specialist

            if user_entity.role == Role.PATIENT and hasattr(user_entity, 'city'):
                patient = PatientOrm(
                    user_id=user_entity.id,
                    city=user_entity.city
                )
                user_orm.patient = patient

            if user_entity.role == Role.ORGANIZATION and hasattr(user_entity, 'locations'):
                organization = OrganizationOrm(
                    user_id=user_entity.id,
                    clinics=getattr(user_entity, 'clinics', []),
                    members=getattr(user_entity, 'members', []),
                    locations=user_entity.locations
                )
                user_orm.organization = organization

            if user_entity.role == Role.ADMIN and hasattr(user_entity, 'admin_role'):
                admin = AdminOrm(
                    user_id=user_entity.id,
                    admin_role=AdminRoles(user_entity.admin_role),
                    is_superadmin=user_entity.is_superadmin
                )
                user_orm.admin = admin

            return user_orm

        except Exception as e:
            self._logger.error(f"Entity to ORM error: {e}", exc_info=True)
            raise

    async def entity_to_orm(self, user_entity: User) -> UserOrm:
        return await self.to_orm(user_entity)


class ClinicOrmEntityAdapter:
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    async def to_entity(self, clinic_orm: ClinicOrm) -> Clinic:
        try:
            work_hours = {}
            if clinic_orm.work_hours:
                for day, hours in clinic_orm.work_hours.items():
                    if hours:
                        work_hours[day] = WorkHours(**hours)

            return Clinic(
                id=clinic_orm.id,
                organization_id=clinic_orm.organization_id,
                name=clinic_orm.name,
                location=clinic_orm.location,
                address=clinic_orm.address,
                created_at=clinic_orm.created_at,
                is_active=clinic_orm.is_active,
                work_hours=work_hours,
                is_24_7=clinic_orm.is_24_7
            )
        except ValidationError as e:
            self._logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self._logger.error(f"ORM to Entity error: {e}", exc_info=True)
            raise

    async def to_orm(self, clinic: Clinic) -> ClinicOrm:
        try:
            work_hours = {
                day: hours.model_dump() if hours else None
                for day, hours in (clinic.work_hours or {}).items()
            }

            return ClinicOrm(
                id=clinic.id,
                organization_id=clinic.organization_id,
                name=clinic.name,
                location=clinic.location,
                address=clinic.address,
                created_at=clinic.created_at,
                is_active=clinic.is_active,
                work_hours=work_hours,
                is_24_7=clinic.is_24_7
            )
        except Exception as e:
            self._logger.error(f"Entity to ORM error: {e}", exc_info=True)
            raise


class AdminOrmEntityAdapter:
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    async def to_entity(self, admin_orm: AdminOrm) -> Admin:
        try:
            return Admin(
                id=admin_orm.id,
                user_id=admin_orm.user_id,
                admin_role=AdminRoles(admin_orm.admin_role),
                is_superadmin=admin_orm.is_superadmin
            )
        except ValidationError as e:
            self._logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self._logger.error(f"ORM to Entity error: {e}", exc_info=True)
            raise

    async def to_orm(self, admin: Admin) -> AdminOrm:
        try:
            return AdminOrm(
                id=admin.id,
                user_id=admin.user_id,
                admin_role=admin.admin_role,
                is_superadmin=admin.is_superadmin
            )
        except Exception as e:
            self._logger.error(f"Entity to ORM error: {e}", exc_info=True)
            raise


class OrderOrmEntityAdapter:
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    async def to_entity(self, order_orm: OrderOrm) -> Order:
        try:
            # Преобразуем ORM enum в доменный enum для роли создателя
            creator_role = Role(order_orm.creator_role.value)

            # Преобразуем ORM enum в доменный enum для статуса
            status = OrderStatus(order_orm.status.value)

            return Order(
                id=order_orm.id,
                creator_id=order_orm.creator_id,
                creator_role=creator_role,
                service_type=order_orm.service_type,
                description=order_orm.description,
                specifications=order_orm.specifications,
                preferred_date=order_orm.preferred_date,
                responses_count=order_orm.responses_count,
                status=status,
                created_at=order_orm.created_at,
                updated_at=order_orm.updated_at,
                patient_id=order_orm.patient_id,
                specialist_id=order_orm.specialist_id,
                clinic_id=order_orm.clinic_id
            )
        except ValidationError as e:
            self._logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self._logger.error(f"ORM to Entity error: {e}", exc_info=True)
            raise

    async def to_orm(self, order: Order) -> OrderOrm:
        try:
            # Преобразуем доменный enum в ORM enum для роли создателя
            creator_role = OrderCreatorRole(order.creator_role.value)

            # Преобразуем доменный enum в ORM enum для статуса
            status = OrderStatus(order.status.value)

            return OrderOrm(
                id=order.id,
                creator_id=order.creator_id,
                creator_role=creator_role,
                service_type=order.service_type,
                description=order.description,
                specifications=order.specifications,
                preferred_date=order.preferred_date,
                responses_count=order.responses_count,
                status=status,
                created_at=order.created_at,
                updated_at=order.updated_at,
                patient_id=order.patient_id,
                specialist_id=order.specialist_id,
                clinic_id=order.clinic_id
            )
        except Exception as e:
            self._logger.error(f"Entity to ORM error: {e}", exc_info=True)
            raise


class ReviewOrmEntityAdapter:
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    async def to_entity(self, review_orm: ReviewOrm) -> Review:
        try:
            # Преобразуем ORM enum в доменный enum для типа цели
            target_type = ReviewTargetType(review_orm.target_type.value)

            return Review(
                id=review_orm.id,
                sender_id=review_orm.sender_id,
                order_id=review_orm.order_id,
                target_id=review_orm.target_id,
                target_type=target_type,
                text=review_orm.text,
                rate=review_orm.rate,
                created_at=review_orm.created_at,
                response=review_orm.response
            )
        except ValidationError as e:
            self._logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self._logger.error(f"ORM to Entity error: {e}", exc_info=True)
            raise

    async def to_orm(self, review: Review) -> ReviewOrm:
        try:
            # Преобразуем доменный enum в ORM enum для типа цели
            target_type = ReviewTargetType(review.target_type.value)

            return ReviewOrm(
                id=review.id,
                sender_id=review.sender_id,
                order_id=review.order_id,
                target_id=review.target_id,
                target_type=target_type,
                text=review.text,
                rate=review.rate,
                created_at=review.created_at,
                response=review.response
            )
        except Exception as e:
            self._logger.error(f"Entity to ORM error: {e}", exc_info=True)
            raise


class ChatOrmEntityAdapter:
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)
        self.message_adapter = MessageOrmEntityAdapter()

    async def to_entity(self, chat_orm: ChatOrm) -> Chat:
        try:
            messages = []
            for msg in chat_orm.messages:
                entity_msg = await self.message_adapter.to_entity(msg)
                if entity_msg:
                    messages.append(entity_msg)

            return Chat(
                chat_id=chat_orm.chat_id,  # Исправлено: теперь передается 'chat_id'
                initiator_id=chat_orm.initiator_id,
                recipient_id=chat_orm.recipient_id,
                order_id=chat_orm.order_id,
                response_id=chat_orm.response_id,
                created_at=chat_orm.created_at,
                messages=messages,
                participants=[chat_orm.initiator_id, chat_orm.recipient_id]  # Добавлено: список участников
            )
        except ValidationError as e:
            self._logger.error(f"Validation error in chat adapter: {e}")
            raise
        except Exception as e:
            self._logger.error(f"ORM to Entity error in chat adapter: {e}", exc_info=True)
            raise

    async def to_orm(self, chat: Chat) -> ChatOrm:
        try:
            messages = []
            for msg in chat.messages:
                messages.append(await self.message_adapter.to_orm(msg))

            return ChatOrm(
                chat_id=chat.chat_id,
                initiator_id=chat.initiator_id,
                recipient_id=chat.recipient_id,
                order_id=chat.order_id,
                response_id=chat.response_id,
                created_at=chat.created_at,
                messages=messages
            )
        except Exception as e:
            self._logger.error(f"Entity to ORM error: {e}", exc_info=True)
            raise


class MessageOrmEntityAdapter:
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    async def to_entity(self, msg_orm: MessageOrm) -> Message:
        try:
            base_data = {
                "message_id": msg_orm.message_id,
                "chat_id": msg_orm.chat_id,
                "sender_id": msg_orm.sender_id,
                "type": msg_orm.type.value if isinstance(msg_orm.type, Enum) else msg_orm.type,
                "sent_at": msg_orm.sent_at,
                "is_read": msg_orm.is_read
            }

            # Обработка полиморфных типов сообщений
            if msg_orm.type == MessageType.TEXT.value:
                # Для текстовых сообщений
                if hasattr(msg_orm, 'text'):
                    return TextMessage(**base_data, text=msg_orm.text)
                elif hasattr(msg_orm, 'text_messages') and msg_orm.text_messages:
                    return TextMessage(**base_data, text=msg_orm.text_messages.text)
                else:
                    self._logger.warning(f"Text message {msg_orm.message_id} has no text content")
                    return TextMessage(**base_data, text="")

            elif msg_orm.type == MessageType.VOICE.value:
                # Для голосовых сообщений
                audio_url = getattr(msg_orm, 'audio_url', None)
                duration_sec = getattr(msg_orm, 'duration_sec', None)

                if audio_url is None and hasattr(msg_orm, 'voice_messages') and msg_orm.voice_messages:
                    audio_url = msg_orm.voice_messages.audio_url
                    duration_sec = msg_orm.voice_messages.duration_sec

                return VoiceMessage(
                    **base_data,
                    audio_url=audio_url or "",
                    duration_sec=duration_sec or 0.0
                )

            elif msg_orm.type == MessageType.FILE.value:
                # Для файлов
                file_url = getattr(msg_orm, 'file_url', None)
                file_name = getattr(msg_orm, 'file_name', None)
                file_size = getattr(msg_orm, 'file_size', None)

                if file_url is None and hasattr(msg_orm, 'file_messages') and msg_orm.file_messages:
                    file_url = msg_orm.file_messages.file_url
                    file_name = msg_orm.file_messages.file_name
                    file_size = msg_orm.file_messages.file_size

                return FileMessage(
                    **base_data,
                    file_url=file_url or "",
                    file_name=file_name or "",
                    file_size=file_size or 0
                )

            elif msg_orm.type == MessageType.IMAGE.value:
                # Для изображений
                image_url = getattr(msg_orm, 'image_url', None)
                width = getattr(msg_orm, 'width', None)
                height = getattr(msg_orm, 'height', None)

                if image_url is None and hasattr(msg_orm, 'image_messages') and msg_orm.image_messages:
                    image_url = msg_orm.image_messages.image_url
                    width = msg_orm.image_messages.width
                    height = msg_orm.image_messages.height

                return ImageMessage(
                    **base_data,
                    image_url=image_url or "",
                    width=width or 0,
                    height=height or 0
                )

            else:
                self._logger.error(f"Unknown message type: {msg_orm.type}")
                return Message(**base_data)

        except Exception as e:
            self._logger.error(f"Error converting ORM to entity: {e}", exc_info=True)
            return None

    async def to_orm(self, msg: Message) -> MessageOrm:
        try:
            self._logger.info(f"ADAPTER: Converting message to ORM: {msg}")

            base_data = {
                "message_id": getattr(msg, "message_id", None),
                "chat_id": msg.chat_id,
                "sender_id": msg.sender_id,
                "type": msg.type,
                "sent_at": msg.sent_at,
                "is_read": msg.is_read
            }
            self._logger.debug(f"Base data: {base_data}")

            # Для текстовых сообщений
            if isinstance(msg, TextMessage):
                self._logger.info("Processing TextMessage")
                text_orm = TextMessageOrm(text=msg.text)
                self._logger.debug(f"TextMessageOrm created: {text_orm}")
                return TextMessageOrm(**base_data, text=msg.text)

            # Для голосовых сообщений
            if isinstance(msg, VoiceMessage):
                self._logger.info("Processing VoiceMessage")
                return VoiceMessageOrm(
                    **base_data,
                    audio_url=msg.audio_url,
                    duration_sec=msg.duration_sec
                )

            # Для файлов
            if isinstance(msg, FileMessage):
                self._logger.info("Processing FileMessage")
                return FileMessageOrm(
                    **base_data,
                    file_url=msg.file_url,
                    file_name=msg.file_name,
                    file_size=msg.file_size
                )

            # Для изображений
            if isinstance(msg, ImageMessage):
                self._logger.info("Processing ImageMessage")
                return ImageMessageOrm(
                    **base_data,
                    image_url=msg.image_url,
                    width=msg.width,
                    height=msg.height
                )

            # Базовый тип
            self._logger.info("Processing base Message")
            return MessageOrm(**base_data)

        except Exception as e:
            self._logger.error(f"ADAPTER: CRITICAL ERROR converting to ORM: {e}", exc_info=True)
            raise


class ResponseOrmEntityAdapter:
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    async def to_entity(self, response_orm: ResponseOrm) -> Response:
        try:
            role = Role(response_orm.role)
            status = ResponseStatus(response_orm.status)

            return Response(
                response_id=response_orm.response_id,
                order_id=response_orm.order_id,
                responser_id=response_orm.responser_id,
                role=role,
                text=response_orm.text,
                created_at=response_orm.created_at,
                status=status,
                updated_at=response_orm.updated_at,
            )
        except ValidationError as e:
            self._logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self._logger.error(f"ORM to Entity error: {e}", exc_info=True)
            raise

    async def to_orm(self, response: Union[Response, ResponseCreate]) -> ResponseOrm:
        try:
            # Обработка разных типов объектов
            status_value = (
                response.status.value
                if hasattr(response, 'status')
                else ResponseStatus.PROPOSED.value
            )

            created_at = (
                response.created_at
                if hasattr(response, 'created_at')
                else datetime.utcnow()
            )

            return ResponseOrm(
                response_id=getattr(response, 'response_id', None),
                order_id=response.order_id,
                responser_id=response.responser_id,
                role=Role(response.role),
                text=response.text,
                created_at=created_at,
                status=status_value,
                updated_at=getattr(response, 'updated_at', None)
            )
        except Exception as e:
            self._logger.error(f"Entity to ORM error: {e}", exc_info=True)
            raise
