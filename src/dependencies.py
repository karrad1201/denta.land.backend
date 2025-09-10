from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from src.infrastructure.repository.database import async_session_maker
from src.infrastructure.adapters.orm_entity_adapter import (
    UserOrmEntityAdapter, ChatOrmEntityAdapter, ClinicOrmEntityAdapter, ResponseOrmEntityAdapter,
    ReviewOrmEntityAdapter, OrderOrmEntityAdapter, AdminOrmEntityAdapter, MessageOrmEntityAdapter)
from src.infrastructure.repository.schemas.user_orm import (
    UserOrm, SpecialistOrm, PatientOrm, OrganizationOrm, AdminOrm, BlockedUserOrm
)
from typing import Type
from src.infrastructure.repository.schemas.clinic_orm import ClinicOrm
from src.infrastructure.repository.schemas.review_orm import ReviewOrm
from src.infrastructure.repository.schemas.order_orm import OrderOrm
from src.infrastructure.repository.schemas.responses_orm import ResponseOrm
from src.infrastructure.repository.schemas.chat_orm import ChatOrm, MessageOrm
from src.domain.entity.users.user import User
from src.domain.entity.users.specialist.specialist import Specialist
from src.domain.entity.users.patient.patient import Patient
from src.domain.entity.users.organization.organization import Organization
from src.domain.entity.users.admin.admin_entity import Admin
from src.domain.entity.clinics.clinic_entity import Clinic
from src.domain.entity.clinics.reviews import Review
from src.domain.entity.orders.order import Order
from src.domain.entity.orders.response import Response
from src.domain.entity.chats.chat_entity import Chat
from src.use_cases.repository.users_usecases import RegistrationUseCase, LoginUseCase, SetSettingsUseCase, AdminUseCase
from src.use_cases.repository.chats_usecases import ChatUseCase
from src.use_cases.repository.clinics_usecases import ClinicUseCase
from src.use_cases.repository.reviews_usecases import ReviewUseCases
from src.use_cases.repository.orders_usecases import OrderUseCase
from src.use_cases.repository.responses_usecases import ResponseUseCase
from src.infrastructure.repository.user.postgres_user_repo import PostgresUserRepo
from src.infrastructure.repository.user.postgres_admin_repo import PostgresAdminRepo
from src.infrastructure.repository.user.postgres_organization_repo import PostgresOrganizationRepo
from src.infrastructure.repository.user.postgres_patient_repo import PostgresPatientRepo
from src.infrastructure.repository.user.postgres_specialist_repo import PostgresSpecialistRepo
from src.infrastructure.repository.clinics.postgres_clinics_repo import PostgresClinicsRepo
from src.infrastructure.repository.clinics.postgres_reviews_repo import PostgresReviewRepo
from src.infrastructure.repository.orders.postgres_orders_repo import PostgresOrdersRepo
from src.infrastructure.repository.orders.postgres_responses_repo import PostgresResponsesRepo
from src.infrastructure.repository.chats.postgres_chats_repo import PostgresChatsRepo

from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status
from jose import JWTError
from dotenv import load_dotenv
import os



async def get_db() -> AsyncSession:
    """Генератор асинхронных сессий для DI"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Адаптеры

# users
async def get_user_adapter() -> UserOrmEntityAdapter:
    return UserOrmEntityAdapter(orm_model=UserOrm, entity_model=User)


async def get_specialist_adapter() -> UserOrmEntityAdapter:
    return UserOrmEntityAdapter(orm_model=SpecialistOrm, entity_model=Specialist)


async def get_patient_adapter() -> UserOrmEntityAdapter:
    return UserOrmEntityAdapter(orm_model=PatientOrm, entity_model=Patient)


async def get_organization_adapter() -> UserOrmEntityAdapter:
    return UserOrmEntityAdapter(orm_model=OrganizationOrm, entity_model=Organization)


async def get_admin_adapter() -> UserOrmEntityAdapter:
    return UserOrmEntityAdapter(orm_model=AdminOrm, entity_model=Admin)


# clinics & reviews
async def get_clinic_adapter() -> ClinicOrmEntityAdapter:
    return ClinicOrmEntityAdapter()



async def get_review_adapter() -> ReviewOrmEntityAdapter:
    return ReviewOrmEntityAdapter(orm_model=ReviewOrm, entity_model=Review)


# orders & responses
async def get_order_adapter() -> OrderOrmEntityAdapter:
    return OrderOrmEntityAdapter(orm_model=OrderOrm, entity_model=Order)


async def get_response_adapter() -> ResponseOrmEntityAdapter:
    return ResponseOrmEntityAdapter(orm_model=ResponseOrm, entity_model=Response)


# chats
async def get_chat_adapter() -> ChatOrmEntityAdapter:
    return ChatOrmEntityAdapter(orm_model=ChatOrm, entity_model=Chat)

async def get_message_adapter() -> MessageOrmEntityAdapter:
    return MessageOrmEntityAdapter()


# Репозитории
# users
async def get_user_repository(
        db: AsyncSession = Depends(get_db),
        adapter: UserOrmEntityAdapter = Depends(get_user_adapter)
) -> PostgresUserRepo:
    from src.infrastructure.repository.user.postgres_user_repo import PostgresUserRepo
    return PostgresUserRepo(session=db, adapter=adapter)


async def get_specialist_repository(
        db: AsyncSession = Depends(get_db),
        adapter: UserOrmEntityAdapter = Depends(get_specialist_adapter)
) -> PostgresSpecialistRepo:
    from src.infrastructure.repository.user.postgres_specialist_repo import PostgresSpecialistRepo
    return PostgresSpecialistRepo(session=db, adapter=adapter)


async def get_patient_repository(
        db: AsyncSession = Depends(get_db),
        adapter: UserOrmEntityAdapter = Depends(get_patient_adapter)
) -> PostgresPatientRepo:
    from src.infrastructure.repository.user.postgres_patient_repo import PostgresPatientRepo
    return PostgresPatientRepo(session=db, adapter=adapter)


async def get_organization_repository(
        db: AsyncSession = Depends(get_db),
        adapter: UserOrmEntityAdapter = Depends(get_organization_adapter)
) -> PostgresOrganizationRepo:
    from src.infrastructure.repository.user.postgres_organization_repo import PostgresOrganizationRepo
    return PostgresOrganizationRepo(session=db, adapter=adapter)


async def get_admin_repository(
        db: AsyncSession = Depends(get_db),
        user_adapter: UserOrmEntityAdapter = Depends(get_admin_adapter),
        admin_adapter: AdminOrmEntityAdapter = Depends(get_admin_adapter)
) -> PostgresAdminRepo:
    from src.infrastructure.repository.user.postgres_admin_repo import PostgresAdminRepo
    return PostgresAdminRepo(session=db, user_adapter=user_adapter, admin_adapter=admin_adapter)


# clinics & reviews
async def get_clinic_repository(
    db: AsyncSession = Depends(get_db),
    adapter: ClinicOrmEntityAdapter = Depends(get_clinic_adapter)
) -> PostgresClinicsRepo:
    return PostgresClinicsRepo(session=db, adapter=adapter)


async def get_review_repository(
        db: AsyncSession = Depends(get_db),
        adapter: ReviewOrmEntityAdapter = Depends(get_review_adapter)
) -> PostgresReviewRepo:
    return PostgresReviewRepo(session=db, adapter=adapter)


# chats
async def get_chat_repository(
        db: AsyncSession = Depends(get_db),
        chat_adapter: ChatOrmEntityAdapter = Depends(get_chat_adapter), message_adapter: MessageOrmEntityAdapter = Depends(get_message_adapter)
) -> PostgresChatsRepo:
    return PostgresChatsRepo(session=db, Chat_adapter=chat_adapter, message_adapter=message_adapter)


# orders & responses
async def get_order_repository(
        db: AsyncSession = Depends(get_db),
        adapter: OrderOrmEntityAdapter = Depends(get_order_adapter)
) -> PostgresOrdersRepo:
    return PostgresOrdersRepo(session=db, adapter=adapter)


async def get_response_repository(
        db: AsyncSession = Depends(get_db),
        adapter: ResponseOrmEntityAdapter = Depends(get_response_adapter)
) -> PostgresResponsesRepo:
    return PostgresResponsesRepo(session=db, adapter=adapter)


# Use Cases
async def get_registration_use_case(
        user_repo: PostgresUserRepo = Depends(get_user_repository),
        specialist_repo: PostgresSpecialistRepo = Depends(get_specialist_repository),
        patient_repo: PostgresPatientRepo = Depends(get_patient_repository),
        org_repo: PostgresOrganizationRepo = Depends(get_organization_repository),
        admin_repo: PostgresAdminRepo = Depends(get_admin_repository),
        user_adapter: UserOrmEntityAdapter = Depends(get_user_adapter)
) -> RegistrationUseCase:
    return RegistrationUseCase(
        user_repo=user_repo,
        specialist_repo=specialist_repo,
        patient_repo=patient_repo,
        org_repo=org_repo,
        admin_repo=admin_repo,
        adapter=user_adapter
    )


async def get_login_use_case(
        user_repo: PostgresUserRepo = Depends(get_user_repository),
        patient_repo: PostgresPatientRepo = Depends(get_patient_repository),
        specialist_repo: PostgresSpecialistRepo = Depends(get_specialist_repository),
        org_repo: PostgresOrganizationRepo = Depends(get_organization_repository),
        admin_repo: PostgresAdminRepo = Depends(get_admin_repository),
        adapter: UserOrmEntityAdapter = Depends(get_user_adapter)
) -> LoginUseCase:
    return LoginUseCase(
        user_repo=user_repo,
        patient_repo=patient_repo,
        specialist_repo=specialist_repo,
        org_repo=org_repo,
        admin_repo=admin_repo,
        adapter=adapter
    )

async def get_admin_use_case(
    admin_repo: PostgresAdminRepo = Depends(get_admin_repository)
) -> AdminUseCase:
    return AdminUseCase(admin_repo=admin_repo)


async def get_settings_use_case(
        user_repo: PostgresUserRepo = Depends(get_user_repository),
        patient_repo: PostgresPatientRepo = Depends(get_patient_repository),
        specialist_repo: PostgresSpecialistRepo = Depends(get_specialist_repository),
        org_repo: PostgresOrganizationRepo = Depends(get_organization_repository),
        admin_repo: PostgresAdminRepo = Depends(get_admin_repository),
        adapter: UserOrmEntityAdapter = Depends(get_user_adapter)
) -> SetSettingsUseCase:
    return SetSettingsUseCase(
        user_repo=user_repo,
        patient_repo=patient_repo,
        specialist_repo=specialist_repo,
        org_repo=org_repo,
        admin_repo=admin_repo,
        adapter=adapter
    )


async def get_clinic_use_case(
    clinic_repo: PostgresClinicsRepo = Depends(get_clinic_repository),
    adapter: ClinicOrmEntityAdapter = Depends(get_clinic_adapter)
) -> ClinicUseCase:
    return ClinicUseCase(clinic_repo=clinic_repo, adapter=adapter)


async def get_orders_use_case(
    order_repo: PostgresOrdersRepo = Depends(get_order_repository),
) -> OrderUseCase:
    return OrderUseCase(orders_repo=order_repo)


async def get_review_use_case(
    review_repo: PostgresReviewRepo = Depends(get_review_repository),
    order_repo: PostgresOrdersRepo = Depends(get_order_repository),
    user_repo: PostgresUserRepo = Depends(get_user_repository),
    clinic_repo: PostgresClinicsRepo = Depends(get_clinic_repository)
) -> ReviewUseCases:
    return ReviewUseCases(
        review_repo=review_repo,
        order_repo=order_repo,
        user_repo=user_repo,
        clinic_repo=clinic_repo
    )


async def get_responses_use_case(
    response_repo: PostgresResponsesRepo = Depends(get_response_repository),
) -> ResponseUseCase:
    return ResponseUseCase(response_repo=response_repo)


async def get_chats_use_case(
    chat_repo: PostgresChatsRepo = Depends(get_chat_repository),
    user_adapter: UserOrmEntityAdapter = Depends(get_user_adapter)
) -> ChatUseCase:
    """ Создает и возвращает экземпляр ChatUseCase """
    return ChatUseCase(chats_repo=chat_repo, adapter=user_adapter)

load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        user_repo: PostgresUserRepo = Depends(get_user_repository)
) -> User:
    try:
        user_id, expiration_time = await user_repo._decode_jwt_token(token)

        from datetime import datetime
        if datetime.utcnow() > datetime.utcfromtimestamp(expiration_time):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await user_repo.get_by_id(int(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

from src.domain.interfaces.user.user_repositiry import IUserRepository
from fastapi import Request
from datetime import datetime

def get_jwt_token_optional(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None

async def get_current_user_optional(
    jwt_token: str = Depends(get_jwt_token_optional),
    user_repo: IUserRepository = Depends(get_user_repository)
):
    if not jwt_token:
        return None
    try:
        user_id, exp = await user_repo._decode_jwt_token(jwt_token)
        if datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
        return await user_repo.get_by_id(user_id)
    except Exception:
        return None
