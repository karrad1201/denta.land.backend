from fastapi import APIRouter, status, Depends, HTTPException, Query
from src.dependencies import get_current_user, get_review_use_case
from src.domain.entity.users.user import User, Role
from src.domain.entity.clinics.reviews import Review, ReviewTargetType
from src.use_cases.repository.reviews_usecases import ReviewUseCases
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

router = APIRouter(prefix='/api/reviews', tags=['Reviews'])


class ReviewTargetTypeEnum(str, Enum):
    specialist = "specialist"
    organization = "organization"
    clinic = "clinic"


class ReviewCreateRequest(BaseModel):
    order_id: int = Field(..., description="ID связанного заказа")
    target_id: int = Field(..., description="ID цели отзыва")
    target_type: ReviewTargetTypeEnum = Field(..., description="Тип цели отзыва")
    text: str = Field(..., min_length=10, max_length=2000, description="Текст отзыва")
    rate: int = Field(..., ge=1, le=10, description="Оценка от 1 до 10")


class ReviewResponse(BaseModel):
    id: int
    sender_id: int
    order_id: int
    target_id: int
    target_type: ReviewTargetTypeEnum
    text: str
    rate: int
    created_at: datetime
    response: Optional[str] = None


class ReviewUpdateRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=2000, description="Текст отзыва")
    rate: int = Field(..., ge=1, le=10, description="Оценка от 1 до 10")


class ReviewResponseRequest(BaseModel):
    response: str = Field(..., min_length=5, max_length=2000, description="Текст ответа")


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
        request: ReviewCreateRequest,
        current_user: User = Depends(get_current_user),
        use_case: ReviewUseCases = Depends(get_review_use_case)
):


    try:
        # Преобразуем enum в доменный тип
        target_type = ReviewTargetType(request.target_type.value)

        review = await use_case.create_review(
            sender_id=current_user.id,
            order_id=request.order_id,
            target_id=request.target_id,
            target_type=target_type,
            text=request.text,
            rate=request.rate
        )

        return ReviewResponse(
            id=review.id,
            sender_id=review.sender_id,
            order_id=review.order_id,
            target_id=review.target_id,
            target_type=ReviewTargetTypeEnum(review.target_type.value),
            text=review.text,
            rate=review.rate,
            created_at=review.created_at,
            response=review.response
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/target/{target_type}/{target_id}", response_model=List[ReviewResponse])
async def get_reviews_for_target(
        target_type: ReviewTargetTypeEnum,
        target_id: int,
        min_rating: Optional[int] = Query(None, ge=1, le=10),
        max_rating: Optional[int] = Query(None, ge=1, le=10),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        use_case: ReviewUseCases = Depends(get_review_use_case)
):
    try:
        # Преобразуем enum в доменный тип
        domain_target_type = ReviewTargetType(target_type.value)

        reviews = await use_case.get_reviews_for_target(
            target_id=target_id,
            target_type=domain_target_type,
            min_rating=min_rating,
            max_rating=max_rating,
            page=page,
            page_size=page_size
        )

        return [
            ReviewResponse(
                id=review.id,
                sender_id=review.sender_id,
                order_id=review.order_id,
                target_id=review.target_id,
                target_type=ReviewTargetTypeEnum(review.target_type.value),
                text=review.text,
                rate=review.rate,
                created_at=review.created_at,
                response=review.response
            )
            for review in reviews
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
        review_id: int,
        current_user: User = Depends(get_current_user),
        use_case: ReviewUseCases = Depends(get_review_use_case)
):
    try:
        review = await use_case.get_review(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        return ReviewResponse(
            id=review.id,
            sender_id=review.sender_id,
            order_id=review.order_id,
            target_id=review.target_id,
            target_type=ReviewTargetTypeEnum(review.target_type.value),
            text=review.text,
            rate=review.rate,
            created_at=review.created_at,
            response=review.response
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
        review_id: int,
        request: ReviewUpdateRequest,
        current_user: User = Depends(get_current_user),
        use_case: ReviewUseCases = Depends(get_review_use_case)
):
    try:
        review = await use_case.get_review(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        if review.sender_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only review author can update"
            )

        updated_review = await use_case.update_review(
            review_id=review_id,
            text=request.text,
            rate=request.rate
        )

        return ReviewResponse(
            id=updated_review.id,
            sender_id=updated_review.sender_id,
            order_id=updated_review.order_id,
            target_id=updated_review.target_id,
            target_type=ReviewTargetTypeEnum(updated_review.target_type.value),
            text=updated_review.text,
            rate=updated_review.rate,
            created_at=updated_review.created_at,
            response=updated_review.response
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{review_id}/respond", response_model=ReviewResponse)
async def respond_to_review(
        review_id: int,
        request: ReviewResponseRequest,
        current_user: User = Depends(get_current_user),
        use_case: ReviewUseCases = Depends(get_review_use_case)
):
    try:
        # Оставляем ответ на отзыв
        review = await use_case.respond_to_review(
            review_id=review_id,
            responder_id=current_user.id,
            response_text=request.response
        )

        return ReviewResponse(
            id=review.id,
            sender_id=review.sender_id,
            order_id=review.order_id,
            target_id=review.target_id,
            target_type=ReviewTargetTypeEnum(review.target_type.value),
            text=review.text,
            rate=review.rate,
            created_at=review.created_at,
            response=review.response
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
        review_id: int,
        current_user: User = Depends(get_current_user),
        use_case: ReviewUseCases = Depends(get_review_use_case)
):
    try:
        # Проверяем, что отзыв существует и принадлежит пользователю
        review = await use_case.get_review(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        if review.sender_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only review author can delete"
            )

        await use_case.delete_review(review_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/user/{user_id}", response_model=List[ReviewResponse])
async def get_user_reviews(
        user_id: int,
        current_user: User = Depends(get_current_user),
        use_case: ReviewUseCases = Depends(get_review_use_case)
):
    try:
        if current_user.id != user_id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these reviews"
            )

        reviews = await use_case.get_user_reviews(user_id)
        return [
            ReviewResponse(
                id=review.id,
                sender_id=review.sender_id,
                order_id=review.order_id,
                target_id=review.target_id,
                target_type=ReviewTargetTypeEnum(review.target_type.value),
                text=review.text,
                rate=review.rate,
                created_at=review.created_at,
                response=review.response
            )
            for review in reviews
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))