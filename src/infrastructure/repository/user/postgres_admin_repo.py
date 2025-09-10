from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.domain.interfaces.user.admin_repository import IAdminRepository
from src.infrastructure.adapters.orm_entity_adapter import UserOrmEntityAdapter, AdminOrmEntityAdapter
from src.infrastructure.repository.schemas.user_orm import UserOrm, AdminOrm, BlockedUserOrm, PatientOrm, \
    OrganizationOrm, SpecialistOrm
import logging
from src.domain.entity.users.admin.admin_entity import Admin, AdminRoles
from sqlalchemy.orm import selectinload


class PostgresAdminRepo(IAdminRepository):
    def __init__(self, session: AsyncSession, user_adapter: UserOrmEntityAdapter, admin_adapter: AdminOrmEntityAdapter):
        self._session = session
        self._adapter = user_adapter
        self._logger = logging.getLogger(__name__)
        self._admin_adapter = admin_adapter

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def create_admin_profile(self, user_id: int, admin_role: AdminRoles, is_superadmin: bool = False):
        try:
            stmt = (
                select(UserOrm)
                .where(UserOrm.id == user_id)
                .options(
                    selectinload(UserOrm.admin),
                    selectinload(UserOrm.blocked_user)
                )
            )
            result = await self._session.execute(stmt)
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                raise ValueError("User not found")

            if user_orm.admin:
                raise ValueError("Admin profile already exists")

            admin_orm = AdminOrm(
                user_id=user_id,
                admin_role=admin_role.value,
                is_superadmin=is_superadmin
            )

            self._session.add(admin_orm)
            await self._session.commit()

            await self._session.refresh(user_orm, attribute_names=['admin', 'blocked_user'])

            return await self._adapter.to_entity(user_orm)

        except Exception as e:
            self._logger.error(f"Error creating admin profile: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def get_admin_profile(self, user_id: int) -> Admin:
        try:
            stmt = (
                select(UserOrm)
                .where(UserOrm.id == user_id)
                .options(
                    selectinload(UserOrm.admin),
                    selectinload(UserOrm.blocked_user)
                )
            )
            result = await self._session.execute(stmt)
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                raise ValueError("User not found")

            if not user_orm.admin:
                raise ValueError("Admin profile not found")

            return await self._adapter.to_entity(user_orm)
        except Exception as e:
            self._logger.error(f"Error getting admin profile: {e}", exc_info=True)
            raise

    async def get_all_users(self, page: int, page_size: int):
        offset = (page - 1) * page_size
        stmt = select(UserOrm).options(
            selectinload(UserOrm.patient),
            selectinload(UserOrm.specialist),
            selectinload(UserOrm.organization),
            selectinload(UserOrm.admin),
            selectinload(UserOrm.blocked_user)
        ).limit(page_size).offset(offset)

        result = await self._session.execute(stmt)
        user_orms = result.scalars().unique().all()
        return [await self._admin_adapter.to_entity(orm) for orm in user_orms]

    async def update_admin_privileges(
            self,
            user_id: int,
            new_role: str,
            is_superadmin: bool
    ):
        try:
            stmt = (
                select(AdminOrm)
                .where(AdminOrm.user_id == user_id)
                .options(
                    selectinload(AdminOrm.user).selectinload(UserOrm.blocked_user)
                )
            )
            result = await self._session.execute(stmt)
            admin_orm = result.scalar_one_or_none()

            if not admin_orm:
                raise ValueError("Admin not found")

            admin_orm.admin_role = new_role
            admin_orm.is_superadmin = is_superadmin

            await self._session.commit()
            await self._session.refresh(admin_orm)

            return await self._adapter.to_entity(admin_orm.user)

        except Exception as e:
            self._logger.error(f"Error updating admin privileges: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def block_user(self, user_id: int, reason: str):
        try:
            user_orm = await self._session.get(UserOrm, user_id)
            if not user_orm:
                raise ValueError("User not found")

            existing_block = await self._session.execute(
                select(BlockedUserOrm).where(BlockedUserOrm.user_id == user_id)
            )
            if existing_block.scalar_one_or_none():
                raise ValueError("User is already blocked")

            blocked_user_orm = BlockedUserOrm(user_id=user_id, reason=reason)
            self._session.add(blocked_user_orm)
            await self._session.commit()
            return True
        except Exception as e:
            self._logger.error(f"Error blocking user: {e}", exc_info=True)
            await self._session.rollback()
            return e

    async def unblock_user(self, user_id: int):
        try:
            blocked_user_orm = await self._session.execute(
                select(BlockedUserOrm).where(BlockedUserOrm.user_id == user_id)
            )
            blocked_user = blocked_user_orm.scalar_one_or_none()

            if not blocked_user:
                raise ValueError("User is not blocked")

            await self._session.delete(blocked_user)
            await self._session.commit()
            return True
        except Exception as e:
            self._logger.error(f"Error unblocking user: {e}", exc_info=True)
            await self._session.rollback()
            return e

    async def delete_user(self, user_id: int):
        try:
            user_orm = await self._session.get(UserOrm, user_id)
            if not user_orm:
                raise ValueError("User not found")
            await self._session.delete(user_orm)
            await self._session.commit()
            return True
        except Exception as e:
            self._logger.error(f"Error deleting user: {e}", exc_info=True)
            await self._session.rollback()
            return e

    async def get_statisctics(self) -> dict:
        try:
            total_users_stmt = select(func.count()).select_from(UserOrm)
            total_users_count = (await self._session.execute(total_users_stmt)).scalar_one()

            patients_stmt = select(func.count()).select_from(PatientOrm)
            patients_count = (await self._session.execute(patients_stmt)).scalar_one()

            specialists_stmt = select(func.count()).select_from(SpecialistOrm)
            specialists_count = (await self._session.execute(specialists_stmt)).scalar_one()

            organizations_stmt = select(func.count()).select_from(OrganizationOrm)
            organizations_count = (await self._session.execute(organizations_stmt)).scalar_one()

            admins_stmt = select(func.count()).select_from(AdminOrm)
            admins_count = (await self._session.execute(admins_stmt)).scalar_one()

            return {
                "total_users": total_users_count,
                "patients": patients_count,
                "specialists": specialists_count,
                "organizations": organizations_count,
                "admins": admins_count
            }
        except Exception as e:
            self._logger.error(f"Error getting statistics: {e}", exc_info=True)
            raise
