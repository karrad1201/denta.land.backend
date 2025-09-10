from abc import ABC, abstractmethod
from src.domain.entity.users.organization.organization import Organization
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession


class IOrganizationRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def create_organization_profile(
            self,
            user_id: int,
            locations: list[str]
    ) -> Organization:
        pass

    @abstractmethod
    async def get_organization_profile(
            self,
            user_id: int
    ) -> Optional[Organization]:
        pass

    @abstractmethod
    async def update_locations(
            self,
            user_id: int,
            new_locations: List[str]
    ) -> Organization:
        pass
