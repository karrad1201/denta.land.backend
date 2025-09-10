from fastapi import APIRouter, status, Depends, HTTPException, Query, Body, Request
from src.dependencies import get_current_user, get_orders_use_case
from src.domain.entity.users.user import User, Role
from src.use_cases.repository.orders_usecases import OrderUseCase
from src.domain.entity.orders.order import OrderStatus, OrderCreate
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix='/api/orders', tags=['Orders'])


class OrderCreateRequest(BaseModel):
    service_type: str
    description: str
    preferred_date: datetime
    specifications: Optional[List[str]] = None
    patient_id: Optional[int] = None
    specialist_id: Optional[int] = None
    clinic_id: Optional[int] = None


class OrderResponse(BaseModel):
    id: int
    creator_id: int
    creator_role: Role
    service_type: str
    description: str
    specifications: List[str]
    preferred_date: datetime
    responses_count: int
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    specialist_id: Optional[int] = None
    clinic_id: Optional[int] = None


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
        request: OrderCreateRequest,
        current_user: User = Depends(get_current_user),
        use_case: OrderUseCase = Depends(get_orders_use_case)
):
    if current_user.role not in [Role.ORGANIZATION, Role.SPECIALIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organizations and specialists can create orders"
        )

    order_data = OrderCreate(
        creator_id=current_user.id,
        creator_role=current_user.role,
        service_type=request.service_type,
        description=request.description,
        specifications=request.specifications or [request.service_type],
        preferred_date=request.preferred_date,
        patient_id=request.patient_id,
        specialist_id=request.specialist_id,
        clinic_id=request.clinic_id
    )

    try:
        order = await use_case.create_order(order_data)
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[OrderResponse])
async def get_my_orders(
        current_user: User = Depends(get_current_user),
        use_case: OrderUseCase = Depends(get_orders_use_case),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100)
):
    try:
        orders = await use_case.get_orders_by_creator(
            creator_id=current_user.id
        )
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
        order_id: int,
        current_user: User = Depends(get_current_user),
        use_case: OrderUseCase = Depends(get_orders_use_case)
):
    try:
        order = await use_case.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        has_access = False

        if order.creator_id == current_user.id:
            has_access = True

        elif order.status == OrderStatus.ACTIVE:
            has_access = True

        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{order_id}/status", status_code=status.HTTP_200_OK)
async def update_order_status(
        order_id: int,
        status: OrderStatus = Body(..., embed=True),
        current_user: User = Depends(get_current_user),
        use_case: OrderUseCase = Depends(get_orders_use_case)
):
    try:
        order = await use_case.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        await use_case.update_order_status(order_id, status)
        return {"message": "Order status updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
        order_id: int,
        current_user: User = Depends(get_current_user),
        use_case: OrderUseCase = Depends(get_orders_use_case)
):
    try:
        order = await use_case.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        await use_case.delete_order(order_id)
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))