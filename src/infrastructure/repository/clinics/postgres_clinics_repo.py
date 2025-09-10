from src.domain.interfaces.clinics.clinics_repository import IClinicsRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.adapters.orm_entity_adapter import ClinicOrmEntityAdapter
from src.infrastructure.repository.schemas.clinic_orm import ClinicOrm
from sqlalchemy import select
import logging


class PostgresClinicsRepo(IClinicsRepository):
    def __init__(self, session: AsyncSession, adapter: ClinicOrmEntityAdapter):
        self._session = session
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def get_clinic(self, clinic_id: int):
        try:
            clinic_orm = await self._session.get(ClinicOrm, clinic_id)
            if clinic_orm:
                return await self._adapter.to_entity(clinic_orm)
            return None
        except Exception as e:
            self._logger.error(f"Error getting clinic: {e}", exc_info=True)
            raise

    async def get_clinics_by_location(self, location: str, limit: int = 100, offset: int = 0):
        try:
            stmt = (
                select(ClinicOrm)
                .where(ClinicOrm.location.ilike(f"%{location}%"))
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            clinics = result.scalars().all()
            return [await self._adapter.to_entity(clinic) for clinic in clinics]
        except Exception as e:
            self._logger.error(f"Error getting clinics by location: {e}", exc_info=True)
            raise

    async def get_clinics_by_organization(self, organization_id: int, limit: int = 100, offset: int = 0):
        try:
            stmt = (
                select(ClinicOrm)
                .where(ClinicOrm.organization_id == organization_id)
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            clinics = result.scalars().all()
            return [await self._adapter.to_entity(clinic) for clinic in clinics]
        except Exception as e:
            self._logger.error(f"Error getting clinics by organization: {e}", exc_info=True)
            raise

    async def create_clinic(self, clinic_data: dict):
        try:
            clinic_orm = ClinicOrm(**clinic_data)
            self._session.add(clinic_orm)
            await self._session.commit()
            await self._session.refresh(clinic_orm)
            return await self._adapter.to_entity(clinic_orm)
        except Exception as e:
            self._logger.error(f"Error creating clinic: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def update_clinic(self, clinic_id: int, update_data: dict):
        try:
            clinic_orm = await self._session.get(ClinicOrm, clinic_id)
            if not clinic_orm:
                return None

            for key, value in update_data.items():
                setattr(clinic_orm, key, value)

            await self._session.commit()
            await self._session.refresh(clinic_orm)
            return await self._adapter.to_entity(clinic_orm)
        except Exception as e:
            self._logger.error(f"Error updating clinic: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def delete_clinic(self, clinic_id: int) -> bool:
        try:
            clinic_orm = await self._session.get(ClinicOrm, clinic_id)
            if clinic_orm:
                await self._session.delete(clinic_orm)
                await self._session.commit()
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error deleting clinic: {e}", exc_info=True)
            await self._session.rollback()
            raise
