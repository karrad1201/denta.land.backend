from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import sqlalchemy as sa
from src.infrastructure.repository.schemas.user_orm import PatientOrm
from src.domain.interfaces.user.patient_repository import IPatientRepository
from src.infrastructure.adapters.orm_entity_adapter import UserOrmEntityAdapter
from src.domain.entity.users.patient.patient import Patient
from src.infrastructure.repository.schemas.user_orm import UserOrm
from sqlalchemy.orm import selectinload
from typing import Dict, Any
import logging


class PostgresPatientRepo(IPatientRepository):
    def __init__(self, session: AsyncSession, adapter: UserOrmEntityAdapter):
        self._session = session
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def create_patient_profile(self, user_id: int, city: str):
        try:
            stmt = (
                select(UserOrm)
                .where(UserOrm.id == user_id)
                .options(selectinload(UserOrm.patient))
            )
            result = await self._session.execute(stmt)
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                raise ValueError("User not found")

            if user_orm.patient:
                raise ValueError("Patient profile already exists")

            patient_orm = PatientOrm(user_id=user_id, city=city)
            self._session.add(patient_orm)
            await self._session.commit()

            await self._session.refresh(user_orm, attribute_names=['patient', 'blocked_user'])

            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            self._logger.error(f"Error creating patient profile: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def get_patient_profile(self, user_id: int) -> Patient:
        stmt = select(PatientOrm).where(PatientOrm.user_id == user_id).options(
            selectinload(PatientOrm.user)
        )
        result = await self.session.execute(stmt)
        patient_orm = result.scalar_one_or_none()

        if patient_orm:
            return await self._adapter.to_entity(patient_orm)
        return None

    async def update_patient_profile(self, user_id: int, update_data: Dict[str, Any]) -> Patient:
        stmt = sa.update(PatientOrm).where(PatientOrm.user_id == user_id).values(**update_data)
        await self._session.execute(stmt)
        await self._session.commit()

        result = await self._session.execute(
            select(PatientOrm)
            .options(selectinload(PatientOrm.user))
            .where(PatientOrm.user_id == user_id)
        )
        updated_patient_orm = result.scalar_one_or_none()
        if not updated_patient_orm:
            raise ValueError("Patient profile not found")
        return await self._adapter.to_entity(updated_patient_orm)

    async def update_city(self, user_id: int, new_city: str):
        try:
            patient_orm = await self._session.get(PatientOrm, user_id)
            if not patient_orm:
                raise ValueError("Patient not found")

            patient_orm.city = new_city
            await self._session.commit()

            # Получаем обновленные данные
            user_orm = await self._session.get(UserOrm, user_id)
            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            self._logger.error(f"Error updating city: {e}", exc_info=True)
            await self._session.rollback()
            raise