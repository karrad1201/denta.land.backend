from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entity.orders.order import Order, OrderStatus, OrderCreate
from src.domain.entity.users.user import Role
from typing import List, Optional


class IOrdersRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def get_order(self, order_id: int) -> Optional[Order]:
        pass

    @abstractmethod
    async def create_order(self, order_data: OrderCreate) -> Order:
        pass

    @abstractmethod
    async def get_orders_by_creator(self, creator_id: int) -> List[Order]:
        pass

    @abstractmethod
    async def get_orders_for_patient(self, patient_id: int) -> List[Order]:
        pass

    @abstractmethod
    async def get_orders_for_specialist(self, specialist_id: int) -> List[Order]:
        pass

    @abstractmethod
    async def get_orders_for_clinic(self, clinic_id: int) -> List[Order]:
        pass

    @abstractmethod
    async def update_order_status(self, order_id: int, status: OrderStatus) -> bool:
        pass

    @abstractmethod
    async def update_order_responses_count(self, order_id: int, increment: int = 1) -> bool:
        pass

    @abstractmethod
    async def delete_order(self, order_id: int) -> bool:
        pass

    @abstractmethod
    async def get_orders_by_service_type(self, service_type: str) -> List[Order]:
        pass

    @abstractmethod
    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        pass
