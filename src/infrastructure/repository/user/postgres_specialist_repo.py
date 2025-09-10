from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.interfaces.user.specialistic_repository import ISpecialistRepository
from src.infrastructure.adapters.orm_entity_adapter import UserOrmEntityAdapter
from typing import List
from sqlalchemy import select
from src.infrastructure.repository.schemas.user_orm import UserOrm, SpecialistOrm
from src.domain.entity.users.specialist.specialist import Specialist
from sqlalchemy.orm import selectinload
import logging


class PostgresSpecialistRepo(ISpecialistRepository):
    def __init__(self, session: AsyncSession, adapter: UserOrmEntityAdapter):
        self._session = session
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def create_specialist_profile(
            self,
            user_id: int,
            specifications: list[str],
            qualification: str = None,
            experience: int = 0
    ):
        try:
            stmt = (
                select(UserOrm)
                .where(UserOrm.id == user_id)
                .options(selectinload(UserOrm.specialist))
            )
            result = await self._session.execute(stmt)
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                raise ValueError("User not found")

            if user_orm.specialist:
                raise ValueError("Specialist profile already exists")

            specialist_orm = SpecialistOrm(
                user_id=user_id,
                specifications=specifications,
                qualification=qualification,
                experience_years=experience
            )

            self._session.add(specialist_orm)
            await self._session.commit()

            await self._session.refresh(user_orm, attribute_names=['specialist', 'blocked_user'])

            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            self._logger.error(f"Error creating specialist profile: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def get_specialist_profile(self, user_id: int) -> Specialist:
        stmt = select(SpecialistOrm).where(SpecialistOrm.user_id == user_id).options(
            selectinload(SpecialistOrm.user)
        )
        result = await self.session.execute(stmt)
        specialist_orm = result.scalar_one_or_none()

        if specialist_orm:
            return await self._adapter.to_entity(specialist_orm)
        return None

    async def update_specialization(self, user_id: int, new_specs: List[str]):
        try:
            specialist_orm = await self._session.get(SpecialistOrm, user_id)
            if not specialist_orm:
                raise ValueError("Specialist not found")

            specialist_orm.specifications = new_specs
            await self._session.commit()

            # Получаем обновленные данные
            user_orm = await self._session.get(UserOrm, user_id)
            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            self._logger.error(f"Error updating specialization: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def add_qualification(self, user_id: int, qualification: str) -> Specialist:
        try:
            specialist_orm = await self._session.get(SpecialistOrm, user_id)
            if not specialist_orm:
                raise ValueError("Specialist not found")

            specialist_orm.qualification = qualification
            await self._session.commit()

            # Получаем обновленные данные
            user_orm = await self._session.get(UserOrm, user_id)
            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            self._logger.error(f"Error adding qualification: {e}", exc_info=True)
            await self._session.rollback()
            raise
