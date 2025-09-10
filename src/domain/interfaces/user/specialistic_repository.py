from abc import ABC, abstractmethod
from src.domain.entity.users.specialist.specialist import Specialist
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession


class ISpecialistRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def create_specialist_profile(
            self,
            user_id: int,
            specifications: list[str],
            qualification: str = None,
            experience: int = 0
    ) -> Specialist:
        pass

    @abstractmethod
    async def get_specialist_profile(self, user_id: int) -> Optional[Specialist]:
        pass

    @abstractmethod
    async def update_specialization(
            self,
            user_id: int,
            new_specs: List[str]
    ) -> Specialist:
        pass

    @abstractmethod
    async def add_qualification(
            self,
            user_id: int,
            qualification: str
    ) -> Specialist:
        pass
