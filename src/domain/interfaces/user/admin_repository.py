from abc import ABC, abstractmethod
from src.domain.entity.users.admin.admin_entity import Admin, AdminRoles
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession


class IAdminRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def create_admin_profile(
            self,
            user_id: int,
            admin_role: AdminRoles,
            is_superadmin: bool = False
    ) -> Admin:
        pass

    @abstractmethod
    async def get_admin_profile(self, user_id: int) -> Optional[Admin]:
        pass

    @abstractmethod
    async def update_admin_privileges(
            self,
            user_id: int,
            new_role: AdminRoles,
            is_superadmin: bool
    ) -> Admin:
        pass
