from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.domain.interfaces.user.user_repositiry import IUserRepository
from src.infrastructure.adapters.orm_entity_adapter import UserOrmEntityAdapter
from src.infrastructure.repository.schemas.user_orm import UserOrm, OrganizationOrm
from src.domain.entity.users.user import User, UserFull
from src.domain.interfaces.user.user_repositiry import SettingsUserData
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from dotenv import load_dotenv
from os import getenv
import logging

load_dotenv()

JWT_SECRET = getenv('JWT_SECRET_KEY', 'test-secret')
JWT_ALGORITHM = getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION = int(getenv('JWT_EXPIRATION', '60'))


class PostgresUserRepo(IUserRepository):
    def __init__(self, session: AsyncSession, adapter: UserOrmEntityAdapter):
        self._session = session
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def create(self, user_entity: User) -> User:
        user_orm = await self._adapter.to_orm(user_entity)

        try:
            self.session.add(user_orm)
            await self.session.commit()

            await self.session.refresh(user_orm, attribute_names=[
                'specialist', 'patient', 'organization', 'admin', 'blocked_user'
            ])

            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            await self.session.rollback()
            logging.error(f"Error creating user: {e}")
            raise

    async def get_by_id(self, id: int):
        try:
            stmt = (
                select(UserOrm)
                .where(UserOrm.id == id)
                .options(
                    selectinload(UserOrm.specialist),
                    selectinload(UserOrm.patient),
                    selectinload(UserOrm.organization).selectinload(OrganizationOrm.clinics),
                    selectinload(UserOrm.admin),
                    selectinload(UserOrm.blocked_user),
                )
            )
            result = await self._session.execute(stmt)
            user_orm = result.scalar_one_or_none()
            if user_orm:
                return await self._adapter.to_entity(user_orm)
            return None
        except Exception as e:
            self._logger.error(f"Error getting user by id: {e}", exc_info=True)
            raise

    async def update(self, user_id: int, update_data: dict) -> bool:
        try:
            stmt = select(UserOrm).where(UserOrm.id == user_id)
            result = await self._session.execute(stmt)
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                raise ValueError(f"User with id {user_id} not found")

            allowed_fields = ['nickname', 'name', 'photo_path', 'country', 'email', 'phone_number', 'password_hash']
            for field, value in update_data.items():
                if field in allowed_fields:
                    setattr(user_orm, field, value)

            self._session.add(user_orm)
            await self._session.commit()
            return True

        except Exception as e:
            self._logger.error(f"Error updating user: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def get_by_nickname(self, nickname: str) -> Optional[UserOrm]:
        try:
            stmt = (
                select(UserOrm)
                .where(UserOrm.nickname == nickname)
                .options(
                    selectinload(UserOrm.specialist),
                    selectinload(UserOrm.patient),
                    selectinload(UserOrm.organization),
                    selectinload(UserOrm.admin),
                    selectinload(UserOrm.blocked_user)
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            self._logger.error(f"Error getting user by nickname: {e}", exc_info=True)
            raise

    async def get_password_hash(self, user_id: int) -> str:
        try:
            stmt = select(UserOrm.password_hash).where(UserOrm.id == user_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            self._logger.error(f"Error getting password hash: {e}", exc_info=True)
            raise

    async def delete(self, user: UserFull) -> bool:
        try:
            user_orm = await self._session.get(UserOrm, user.id)
            if user_orm:
                await self._session.delete(user_orm)
                await self._session.commit()
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error deleting user: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def _verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    async def _generate_jwt_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(minutes=int(JWT_EXPIRATION))
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    async def _decode_jwt_token(self, token: str):
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['sub'], payload['exp']

    async def check_register(self, nickname: str, password: str) -> str:
        try:
            user_orm = await self.get_by_nickname(nickname)
            if not user_orm:
                raise ValueError("Пользователь с таким никнеймом не найден")

            if not await self._verify_password(password, user_orm.password_hash):
                raise ValueError("Неверный пароль")

            return await self._generate_jwt_token(user_orm.id)
        except Exception as e:
            self._logger.error(f"Error during registration check: {e}", exc_info=True)
            raise

    async def set_settings(self, user: SettingsUserData) -> bool:
        try:
            user_orm = await self._session.get(UserOrm, user.id)
            if not user_orm:
                raise ValueError("Пользователь не найден")

            user_orm.settings = user.settings
            await self._session.commit()
            return True
        except Exception as e:
            self._logger.error(f"Error setting user settings: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def check_nickname_exists(self, nickname: str) -> bool:
        try:
            return await self.get_by_nickname(nickname) is not None
        except Exception as e:
            self._logger.error(f"Error checking nickname existence: {e}", exc_info=True)
            raise

    async def check_email_exists(self, email: str) -> bool:
        try:
            stmt = select(UserOrm).where(UserOrm.email == email)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            self._logger.error(f"Error checking email existence: {e}", exc_info=True)
            raise
