from fastapi import APIRouter, status, Depends, HTTPException, Query, Request
from src.dependencies import get_current_user, get_responses_use_case, get_orders_use_case
from src.domain.entity.users.user import User
from src.domain.entity.users.user import Role
from src.use_cases.repository.responses_usecases import ResponseUseCase
from src.use_cases.repository.orders_usecases import OrderUseCase
from src.domain.entity.orders.response import Response, ResponseCreate, ResponseStatus
from src.domain.entity.orders.order import OrderStatus
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.exceptions import (
    ResponseNotFoundError,
    DuplicateResponseError,
    InvalidResponseActionError
)

router = APIRouter(prefix='/api/responses', tags=['Responses'])


class ResponseCreateRequest(BaseModel):
    order_id: int
    text: str



class ResponseResponse(BaseModel):
    response_id: int
    order_id: int
    responser_id: int
    role: str
    text: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]


@router.post("/", response_model=ResponseResponse, status_code=status.HTTP_201_CREATED)
async def create_response(
        request: ResponseCreateRequest,
        current_user: User = Depends(get_current_user),
        response_uc: ResponseUseCase = Depends(get_responses_use_case),
        order_uc: OrderUseCase = Depends(get_orders_use_case)
):
    order = await order_uc.get_order(request.order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status != OrderStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot respond to inactive order"
        )

    if order.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot respond to your own order"
        )

    response_data = ResponseCreate(
        order_id=request.order_id,
        responser_id=current_user.id,
        role=current_user.role,
        text=request.text
    )

    try:
        response = await response_uc.create_response(response_data)

        await order_uc.update_order_responses_count(
            order_id=request.order_id,
            increment=1
        )

        return ResponseResponse(
            response_id=response.response_id,
            order_id=response.order_id,
            responser_id=response.responser_id,
            role=response.role.value,
            text=response.text,
            status=response.status.value,
            created_at=response.created_at,
            updated_at=response.updated_at
        )
    except DuplicateResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating response: {str(e)}"
        )


@router.get("/{response_id}", response_model=ResponseResponse)
async def get_response(
        response_id: int,
        current_user: User = Depends(get_current_user),
        response_uc: ResponseUseCase = Depends(get_responses_use_case)
):
    """Get a specific response by ID"""
    try:
        response = await response_uc.get_response(response_id)
        return ResponseResponse(
            response_id=response.response_id,
            order_id=response.order_id,
            responser_id=response.responser_id,
            role=response.role.value,
            text=response.text,
            status=response.status.value,
            created_at=response.created_at,
            updated_at=response.updated_at
        )
    except ResponseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting response: {str(e)}"
        )


@router.get("/order/{order_id}", response_model=List[ResponseResponse])
async def get_responses_for_order(
        order_id: int,
        current_user: User = Depends(get_current_user),
        response_uc: ResponseUseCase = Depends(get_responses_use_case),
        status: Optional[ResponseStatus] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100)
):
    try:
        responses = await response_uc.get_order_responses(
            order_id=order_id,
            status=status,
            page=page,
            page_size=page_size
        )

        return [
            ResponseResponse(
                response_id=r.response_id,
                order_id=r.order_id,
                responser_id=r.responser_id,
                role=r.role.value,
                text=r.text,
                status=r.status.value,
                created_at=r.created_at,
                updated_at=r.updated_at
            ) for r in responses
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting responses: {str(e)}"
        )


@router.put("/{response_id}/accept", response_model=ResponseResponse)
async def accept_response(
        response_id: int,
        current_user: User = Depends(get_current_user),
        response_uc: ResponseUseCase = Depends(get_responses_use_case),
        order_uc: OrderUseCase = Depends(get_orders_use_case)
):
    try:
        response = await response_uc.get_response(response_id)

        order = await order_uc.get_order(response.order_id)
        if not order:
            raise ValueError("Order not found")

        if order.creator_id != current_user.id:
            raise InvalidResponseActionError(
                "Only order creator can accept responses"
            )


        if order.status != OrderStatus.ACTIVE:
            raise InvalidResponseActionError(
                "Cannot accept responses for inactive orders"
            )


        if response.status != ResponseStatus.PROPOSED:
            raise InvalidResponseActionError(
                "Only proposed responses can be accepted"
            )

        updated_response = await response_uc.update_response_status(
            response_id=response_id,
            status=ResponseStatus.TAKEN
        )


        await order_uc.update_order_status(
            order_id=order.id,
            status=OrderStatus.COMPLETED
        )

        other_responses = await response_uc.get_order_responses(
            order_id=order.id,
            status=ResponseStatus.PROPOSED
        )

        for resp in other_responses:
            if resp.response_id != response_id:
                await response_uc.update_response_status(
                    response_id=resp.response_id,
                    status=ResponseStatus.DENIED
                )

        return ResponseResponse(
            response_id=updated_response.response_id,
            order_id=updated_response.order_id,
            responser_id=updated_response.responser_id,
            role=updated_response.role.value,
            text=updated_response.text,
            status=updated_response.status.value,
            created_at=updated_response.created_at,
            updated_at=updated_response.updated_at
        )

    except (ResponseNotFoundError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidResponseActionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accepting response: {str(e)}"
        )


@router.put("/{response_id}/deny", response_model=ResponseResponse)
async def deny_response(
        response_id: int,
        current_user: User = Depends(get_current_user),
        response_uc: ResponseUseCase = Depends(get_responses_use_case),
        order_uc = Depends(get_orders_use_case)
):
    try:

        response = await response_uc.get_response(response_id)

        is_creator = response.responser_id == current_user.id
        is_order_creator = False

        if not is_creator:
            order = await order_uc.get_order(response.order_id)
            is_order_creator = order and order.creator_id == current_user.id

        if not (is_creator or is_order_creator):
            raise InvalidResponseActionError(
                "Only response creator or order creator can deny responses"
            )

        if response.status != ResponseStatus.PROPOSED:
            raise InvalidResponseActionError(
                "Only proposed responses can be denied"
            )

        updated_response = await response_uc.update_response_status(
            response_id=response_id,
            status=ResponseStatus.DENIED
        )

        return ResponseResponse(
            response_id=updated_response.response_id,
            order_id=updated_response.order_id,
            responser_id=updated_response.responser_id,
            role=updated_response.role.value,
            text=updated_response.text,
            status=updated_response.status.value,
            created_at=updated_response.created_at,
            updated_at=updated_response.updated_at
        )

    except ResponseNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidResponseActionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error denying response: {str(e)}"
        )


@router.delete("/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_response(
        response_id: int,
        current_user: User = Depends(get_current_user),
        response_uc: ResponseUseCase = Depends(get_responses_use_case),
        order_uc: OrderUseCase = Depends(get_orders_use_case)
):
    try:
        response = await response_uc.get_response(response_id)
        if response.responser_id != current_user.id:
            raise InvalidResponseActionError(
                "Only response creator can delete responses"
            )

        if response.status != ResponseStatus.PROPOSED:
            raise InvalidResponseActionError(
                "Only proposed responses can be deleted"
            )

        success = await response_uc.delete_response(response_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete response"
            )

        await order_uc.update_order_responses_count(
            order_id=response.order_id,
            increment=-1
        )

    except ResponseNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidResponseActionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting response: {str(e)}"
        )