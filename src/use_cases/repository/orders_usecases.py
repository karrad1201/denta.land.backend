from src.domain.interfaces.orders.orders_repository import IOrdersRepository
from src.domain.entity.orders.order import Order, OrderStatus, OrderCreate
from src.domain.entity.users.user import Role
import logging
from typing import List, Optional

class OrderUseCase:
    def __init__(
            self,
            orders_repo: IOrdersRepository,
    ):
        self._order_repo = orders_repo
        self._logger = logging.getLogger(__name__)

    async def create_order(self, order_data: OrderCreate) -> Order:
        try:
            return await self._order_repo.create_order(order_data)
        except Exception as e:
            self._logger.error(f"Error creating order: {e}", exc_info=True)
            raise

    async def get_order(self, order_id: int) -> Optional[Order]:
        try:
            return await self._order_repo.get_order(order_id)
        except Exception as e:
            self._logger.error(f"Error getting order: {e}", exc_info=True)
            raise

    async def get_orders_by_creator(self, creator_id: int) -> List[Order]:
        try:
            return await self._order_repo.get_orders_by_creator(creator_id)
        except Exception as e:
            self._logger.error(f"Error getting orders by creator: {e}", exc_info=True)
            raise

    async def get_orders_for_user(
        self,
        user_id: int,
        role: Role,
        page: int = 1,
        page_size: int = 10
    ) -> List[Order]:
        try:
            if role == Role.PATIENT:
                return await self._order_repo.get_orders_for_patient(user_id)
            elif role == Role.SPECIALIST:
                return await self._order_repo.get_orders_for_specialist(user_id)
            elif role == Role.ORGANIZATION:
                return await self._order_repo.get_orders_for_clinic(user_id)
            else:
                raise ValueError(f"Invalid role for order access: {role}")
        except Exception as e:
            self._logger.error(f"Error getting user orders: {e}", exc_info=True)
            raise

    async def update_order_status(self, order_id: int, status: OrderStatus) -> bool:
        try:
            return await self._order_repo.update_order_status(order_id, status)
        except Exception as e:
            self._logger.error(f"Error updating order status: {e}", exc_info=True)
            raise

    async def update_order_responses_count(self, order_id: int, increment: int = 1) -> bool:
        try:
            return await self._order_repo.update_order_responses_count(order_id, increment)
        except Exception as e:
            self._logger.error(f"Error updating responses count: {e}", exc_info=True)
            raise

    async def delete_order(self, order_id: int) -> bool:
        try:
            return await self._order_repo.delete_order(order_id)
        except Exception as e:
            self._logger.error(f"Error deleting order: {e}", exc_info=True)
            raise

    async def get_orders_by_service_type(self, service_type: str) -> List[Order]:
        try:
            return await self._order_repo.get_orders_by_service_type(service_type)
        except Exception as e:
            self._logger.error(f"Error getting orders by service type: {e}", exc_info=True)
            raise

    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        try:
            return await self._order_repo.get_orders_by_status(status)
        except Exception as e:
            self._logger.error(f"Error getting orders by status: {e}", exc_info=True)
            raise