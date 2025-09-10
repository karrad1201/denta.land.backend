from src.domain.interfaces.orders.responses_repository import IResponseRepository
from src.domain.entity.orders.response import Response, ResponseStatus, ResponseCreate
from typing import List, Optional
import logging
from src.domain.entity.users.user import Role
from src.exceptions import ResponseNotFoundError, DuplicateResponseError

class ResponseUseCase:
    def __init__(
        self,
        response_repo: IResponseRepository,
    ):
        self._response_repo = response_repo
        self._logger = logging.getLogger(__name__)

    async def create_response(self, response_data: ResponseCreate) -> Response:
        try:
            return await self._response_repo.create_response(response_data)
        except Exception as e:
            self._logger.error(f"Error creating response: {e}", exc_info=True)
            raise DuplicateResponseError(f"{e}") from e

    async def get_response(self, response_id: int) -> Response:
        response = await self._response_repo.get_response(response_id)
        if not response:
            raise ResponseNotFoundError(f"Response with ID {response_id} not found")
        return response

    async def get_order_responses(
        self,
        order_id: int,
        status: Optional[ResponseStatus] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Response]:
        try:
            return await self._response_repo.get_order_responses(order_id, status)
        except Exception as e:
            self._logger.error(f"Error getting order responses: {e}", exc_info=True)
            raise

    async def get_user_responses(
        self,
        user_id: int,
        role: Optional[Role] = None,
        status: Optional[ResponseStatus] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Response]:
        try:
            return await self._response_repo.get_user_responses(user_id, role, status)
        except Exception as e:
            self._logger.error(f"Error getting user responses: {e}", exc_info=True)
            raise

    async def update_response_status(
        self,
        response_id: int,
        status: ResponseStatus
    ) -> Response:
        try:
            response = await self._response_repo.update_response_status(response_id, status)
            if not response:
                raise ResponseNotFoundError(f"Response with ID {response_id} not found")
            return response
        except Exception as e:
            self._logger.error(f"Error updating response status: {e}", exc_info=True)
            raise

    async def delete_response(self, response_id: int) -> bool:
        try:
            return await self._response_repo.delete_response(response_id)
        except Exception as e:
            self._logger.error(f"Error deleting response: {e}", exc_info=True)
            raise

    async def response_exists(
        self,
        order_id: int,
        responser_id: int
    ) -> bool:
        try:
            return await self._response_repo.response_exists(order_id, responser_id)
        except Exception as e:
            self._logger.error(f"Error checking response existence: {e}", exc_info=True)
            raise