from src.infrastructure.adapters.orm_entity_adapter import ClinicOrmEntityAdapter
from src.domain.interfaces.clinics.clinics_repository import IClinicsRepository
import logging


class ClinicUseCase:
    def __init__(
            self,
            clinic_repo: IClinicsRepository,
            adapter: ClinicOrmEntityAdapter
    ):
        self._clinic_repo = clinic_repo
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    async def get_clinic(self, clinic_id: int):
        try:
            return await self._clinic_repo.get_clinic(clinic_id)
        except Exception as e:
            self._logger.error(f"Error getting clinic: {e}")
            return e

    async def get_clinics_by_location(self, location: str, page: int = 1, page_size: int = 10):
        try:
            offset = (page - 1) * page_size
            return self._clinic_repo.get_clinics_by_location(
                location,
                limit=page_size,
                offset=offset
            )
        except Exception as e:
            self._logger.error(f"Error getting clinics by location: {e}")
            return e

    async def get_clinics_by_organization(self, organization_id: int, page: int = 1, page_size: int = 10):
        try:
            offset = (page - 1) * page_size
            return await self._clinic_repo.get_clinics_by_organization(
                organization_id,
                limit=page_size,
                offset=offset
            )
        except Exception as e:
            self._logger.error(f"Error getting clinics by organization: {e}")
            return e

    async def create_clinic(self, clinic_data: dict):
        try:
                return await self._clinic_repo.create_clinic(clinic_data)
        except Exception as e:
            self._logger.error(f"Error creating clinic: {e}")
            return e

    async def update_clinic(self, clinic_id: int, update_data: dict):
        try:
            return await self._clinic_repo.update_clinic(clinic_id, update_data)
        except Exception as e:
            self._logger.error(f"Error updating clinic: {e}")
            return e

    async def delete_clinic(self, clinic_id: int):
        try:
            return await self._clinic_repo.delete_clinic(clinic_id)
        except Exception as e:
            self._logger.error(f"Error deleting clinic: {e}")
            return e