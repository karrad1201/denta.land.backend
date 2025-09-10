from src.domain.interfaces.orders.responses_repository import IResponseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.adapters.orm_entity_adapter import ResponseOrmEntityAdapter
from src.domain.entity.orders.response import Response, ResponseStatus, ResponseCreate
from typing import List, Optional
from sqlalchemy import select, delete, func
from src.infrastructure.repository.schemas.responses_orm import ResponseOrm
from src.domain.entity.users.user import Role
import logging


class PostgresResponsesRepo(IResponseRepository):
    def __init__(self, session: AsyncSession, adapter: ResponseOrmEntityAdapter):
        self._session = session
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def create_response(self, response: ResponseCreate) -> Response:
        try:
            if await self.response_exists(response.order_id, response.responser_id):
                raise ValueError("Response already exists for this order and user")

            response_domain = ResponseCreate(
                order_id=response.order_id,
                responser_id=response.responser_id,
                role=response.role,
                text=response.text
            )

            response_orm = await self._adapter.to_orm(response_domain)
            self._session.add(response_orm)
            await self._session.commit()
            await self._session.refresh(response_orm)

            return await self._adapter.to_entity(response_orm)
        except Exception as e:
            self._logger.error(f"Error creating response: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def update_response_status(self, response_id: int, status: ResponseStatus) -> Optional[Response]:
        try:
            stmt = select(ResponseOrm).where(ResponseOrm.response_id == response_id)
            result = await self._session.execute(stmt)
            response_orm = result.scalar_one_or_none()

            if not response_orm:
                return None

            response_orm.status = status.value
            response_orm.updated_at = func.now()

            await self._session.commit()
            await self._session.refresh(response_orm)

            return await self._adapter.to_entity(response_orm)
        except Exception as e:
            self._logger.error(f"Error updating response status: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def get_response(self, response_id: int) -> Optional[Response]:
        try:
            stmt = select(ResponseOrm).where(ResponseOrm.response_id == response_id)
            result = await self._session.execute(stmt)
            response_orm = result.scalar_one_or_none()

            if not response_orm:
                return None

            return await self._adapter.to_entity(response_orm)
        except Exception as e:
            self._logger.error(f"Error getting response: {e}", exc_info=True)
            raise

    async def get_order_responses(
            self,
            order_id: int,
            status: Optional[ResponseStatus] = None
    ) -> List[Response]:
        try:
            stmt = select(ResponseOrm).where(ResponseOrm.order_id == order_id)

            if status:
                stmt = stmt.where(ResponseOrm.status == status.value)

            result = await self._session.execute(stmt)
            responses_orm = result.scalars().all()

            return [await self._adapter.to_entity(resp) for resp in responses_orm]
        except Exception as e:
            self._logger.error(f"Error getting order responses: {e}", exc_info=True)
            raise

    async def get_user_responses(
            self,
            user_id: int,
            role: Optional[Role] = None,
            status: Optional[ResponseStatus] = None
    ) -> List[Response]:
        try:
            stmt = select(ResponseOrm).where(ResponseOrm.responser_id == user_id)

            if role:
                stmt = stmt.where(ResponseOrm.role == role.value)

            if status:
                stmt = stmt.where(ResponseOrm.status == status.value)

            result = await self._session.execute(stmt)
            responses_orm = result.scalars().all()

            return [await self._adapter.to_entity(resp) for resp in responses_orm]
        except Exception as e:
            self._logger.error(f"Error getting user responses: {e}", exc_info=True)
            raise

    async def delete_response(self, response_id: int) -> bool:
        try:
            stmt = delete(ResponseOrm).where(ResponseOrm.response_id == response_id)
            result = await self._session.execute(stmt)
            await self._session.commit()

            return result.rowcount > 0
        except Exception as e:
            self._logger.error(f"Error deleting response: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def response_exists(
            self,
            order_id: int,
            responser_id: int
    ) -> bool:
        try:
            stmt = select(ResponseOrm).where(
                (ResponseOrm.order_id == order_id) &
                (ResponseOrm.responser_id == responser_id)
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            self._logger.error(f"Error checking response existence: {e}", exc_info=True)
            raise
