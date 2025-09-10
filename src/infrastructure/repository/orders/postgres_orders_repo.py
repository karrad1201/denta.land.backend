from src.domain.interfaces.orders.orders_repository import IOrdersRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.infrastructure.adapters.orm_entity_adapter import OrderOrmEntityAdapter
from src.domain.entity.orders.order import Order, OrderStatus
from src.infrastructure.repository.schemas.order_orm import OrderOrm
from src.domain.entity.orders.order import OrderCreate
from typing import List, Optional


class PostgresOrdersRepo(IOrdersRepository):
    def __init__(self, session: AsyncSession, adapter: OrderOrmEntityAdapter):
        self._session = session
        self._adapter = adapter

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def get_order(self, order_id: int) -> Optional[Order]:
        stmt = select(OrderOrm).where(OrderOrm.id == order_id)
        result = await self._session.execute(stmt)
        order_orm = result.scalar_one_or_none()
        if not order_orm:
            return None
        return await self._adapter.to_entity(order_orm)

    async def create_order(self, order_data: OrderCreate) -> Order:
        # Преобразуем доменную модель в словарь для ORM
        order_dict = order_data.dict()
        order_orm = OrderOrm(**order_dict)

        self._session.add(order_orm)
        await self._session.commit()
        await self._session.refresh(order_orm)
        return await self._adapter.to_entity(order_orm)

    async def get_orders_by_creator(self, creator_id: int) -> List[Order]:
        stmt = select(OrderOrm).where(OrderOrm.creator_id == creator_id)
        result = await self._session.execute(stmt)
        orders = result.scalars().all()
        return [await self._adapter.to_entity(order) for order in orders]

    async def get_orders_for_patient(self, patient_id: int) -> List[Order]:
        stmt = select(OrderOrm).where(OrderOrm.patient_id == patient_id)
        result = await self._session.execute(stmt)
        orders = result.scalars().all()
        return [await self._adapter.to_entity(order) for order in orders]

    async def get_orders_for_specialist(self, specialist_id: int) -> List[Order]:
        stmt = select(OrderOrm).where(OrderOrm.specialist_id == specialist_id)
        result = await self._session.execute(stmt)
        orders = result.scalars().all()
        return [await self._adapter.to_entity(order) for order in orders]

    async def get_orders_for_clinic(self, clinic_id: int) -> List[Order]:
        stmt = select(OrderOrm).where(OrderOrm.clinic_id == clinic_id)
        result = await self._session.execute(stmt)
        orders = result.scalars().all()
        return [await self._adapter.to_entity(order) for order in orders]

    async def update_order_status(self, order_id: int, status: OrderStatus) -> bool:
        stmt = (
            update(OrderOrm)
            .where(OrderOrm.id == order_id)
            .values(status=status)
        )
        await self._session.execute(stmt)
        await self._session.commit()
        return True

    async def update_order_responses_count(self, order_id: int, increment: int = 1) -> bool:
        stmt = (
            update(OrderOrm)
            .where(OrderOrm.id == order_id)
            .values(responses_count=OrderOrm.responses_count + increment)
        )
        await self._session.execute(stmt)
        await self._session.commit()
        return True

    async def delete_order(self, order_id: int) -> bool:
        order = await self._session.get(OrderOrm, order_id)
        if not order:
            return False

        await self._session.delete(order)
        await self._session.commit()
        return True

    async def get_orders_by_service_type(self, service_type: str) -> List[Order]:
        stmt = select(OrderOrm).where(OrderOrm.service_type == service_type)
        result = await self._session.execute(stmt)
        orders = result.scalars().all()
        return [await self._adapter.to_entity(order) for order in orders]

    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        stmt = select(OrderOrm).where(OrderOrm.status == status)
        result = await self._session.execute(stmt)
        orders = result.scalars().all()
        return [await self._adapter.to_entity(order) for order in orders]
