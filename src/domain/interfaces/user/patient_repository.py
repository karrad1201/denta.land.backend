from abc import ABC, abstractmethod
from src.domain.entity.users.patient.patient import Patient
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession


class IPatientRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def create_patient_profile(self, user_id: int, city: str) -> Patient:
        pass

    @abstractmethod
    async def get_patient_profile(self, user_id: int) -> Optional[Patient]:
        pass

    @abstractmethod
    async def update_city(self, user_id: int, new_city: str) -> Patient:
        pass
