from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.domain.interfaces.user.organization_repository import IOrganizationRepository
from src.infrastructure.adapters.orm_entity_adapter import UserOrmEntityAdapter
from typing import List
from src.infrastructure.repository.schemas.user_orm import UserOrm, OrganizationOrm
from src.domain.entity.users.organization.organization import Organization
import logging
from sqlalchemy.orm import selectinload


class PostgresOrganizationRepo(IOrganizationRepository):
    def __init__(self, session: AsyncSession, adapter: UserOrmEntityAdapter):
        self._session = session
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def create_organization_profile(self, user_id: int, locations: list[str]):
        try:
            stmt = (
                select(UserOrm)
                .where(UserOrm.id == user_id)
                .options(selectinload(UserOrm.organization))
            )
            result = await self._session.execute(stmt)
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                raise ValueError("User not found")

            if user_orm.organization:
                raise ValueError("Organization profile already exists")

            organization_orm = OrganizationOrm(
                user_id=user_id,
                locations=locations,
                clinics=[],
                members=[]
            )

            self._session.add(organization_orm)
            await self._session.commit()

            await self._session.refresh(user_orm, attribute_names=['organization', 'blocked_user'])

            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            self._logger.error(f"Error creating organization profile: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def get_organization_profile(self, user_id: int) -> Organization:
        stmt = (
            select(OrganizationOrm)
            .where(OrganizationOrm.user_id == user_id)
            .options(selectinload(OrganizationOrm.clinics))
        )
        result = await self._session.execute(stmt)
        organization_orm = result.scalars().first()

        if not organization_orm:
            raise Exception("Organization profile not found")

        return await self._adapter.to_entity(organization_orm)

    async def update_locations(self, user_id: int, new_locations: List[str]) -> Organization:
        try:
            organization_orm = await self._session.get(OrganizationOrm, user_id)
            if not organization_orm:
                raise ValueError("Organization not found")

            organization_orm.locations = new_locations
            await self._session.commit()

            # Получаем обновленные данные
            user_orm = await self._session.get(UserOrm, user_id)
            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            self._logger.error(f"Error updating locations: {e}", exc_info=True)
            await self._session.rollback()
            raise
