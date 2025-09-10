from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entity.orders.response import Response, ResponseStatus, ResponseCreate
from typing import List, Optional
from src.domain.entity.users.user import Role


class IResponseRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def create_response(self, response: ResponseCreate) -> Response:
        pass

    @abstractmethod
    async def update_response_status(
            self,
            response_id: int,
            status: ResponseStatus
    ) -> Optional[Response]:
        pass

    @abstractmethod
    async def get_response(self, response_id: int) -> Optional[Response]:
        pass

    @abstractmethod
    async def get_order_responses(
            self,
            order_id: int,
            status: Optional[ResponseStatus] = None
    ) -> List[Response]:
        pass

    @abstractmethod
    async def get_user_responses(
            self,
            user_id: int,
            role: Optional[Role] = None,
            status: Optional[ResponseStatus] = None
    ) -> List[Response]:
        pass

    @abstractmethod
    async def delete_response(self, response_id: int) -> bool:
        pass

    @abstractmethod
    async def response_exists(
            self,
            order_id: int,
            responser_id: int
    ) -> bool:
        pass
