from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entity.clinics.clinic_entity import Clinic


class IClinicsRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    def get_clinic(self, clinic_id: int) -> Clinic:
        pass

    @abstractmethod
    def get_clinics_by_location(self, location: str) -> list[Clinic]:
        pass

    @abstractmethod
    def get_clinics_by_organization(self, organization_id: int) -> list[Clinic]:
        pass

    @abstractmethod
    def create_clinic(self, clinic: Clinic) -> bool:
        pass

    @abstractmethod
    def update_clinic(self, clinic: Clinic) -> bool:
        pass

    @abstractmethod
    def delete_clinic(self, clinic_id: int) -> bool:
        pass
