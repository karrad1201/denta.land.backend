from src.domain.entity.clinics.reviews import Review, ReviewTargetType
from src.domain.interfaces.clinics.reviews_repository import IReviewRepository
from src.domain.interfaces.orders.orders_repository import IOrdersRepository
from src.domain.interfaces.user.user_repositiry import IUserRepository
from src.domain.interfaces.clinics.clinics_repository import IClinicsRepository
from src.domain.entity.users.user import Role
from datetime import datetime
import logging
from typing import Optional
from src.domain.entity.orders.order import OrderStatus


class ReviewUseCases:
    def __init__(
            self,
            review_repo: IReviewRepository,
            order_repo: IOrdersRepository,
            user_repo: IUserRepository,
            clinic_repo: IClinicsRepository
    ):
        self._review_repo = review_repo
        self._order_repo = order_repo
        self._logger = logging.getLogger(__name__)
        self._user_repo = user_repo
        self._clinic_repo = clinic_repo

    async def create_review(
            self,
            sender_id: int,
            order_id: int,
            target_id: int,
            target_type: ReviewTargetType,
            text: str,
            rate: int
    ) -> Review:
        try:
            sender = await self._user_repo.get_by_id(sender_id)
            if not sender:
                raise ValueError("Sender not found")

            order = await self._order_repo.get_order(order_id)
            if not order:
                raise ValueError("Order not found")

            if order.status == OrderStatus.ACTIVE:
                raise ValueError("Reviews can only be created for inactive orders")

            if await self._review_repo.has_review_for_order(order_id, sender_id, target_id):
                raise ValueError("Review already exists for this order and target")

            if sender.role == Role.PATIENT:
                if target_type not in {
                    ReviewTargetType.SPECIALIST,
                    ReviewTargetType.ORGANIZATION,
                    ReviewTargetType.CLINIC
                }:
                    raise ValueError("Patients can only review specialists, organizations or clinics")

            elif sender.role == Role.SPECIALIST:
                if target_type not in {ReviewTargetType.ORGANIZATION, ReviewTargetType.CLINIC}:
                    raise ValueError("Specialists can only review organizations or clinics")

            elif sender.role == Role.ORGANIZATION:
                if target_type != ReviewTargetType.SPECIALIST:
                    raise ValueError("Organizations can only review specialists")

            review = Review(
                sender_id=sender_id,
                order_id=order_id,
                target_id=target_id,
                target_type=target_type,
                text=text,
                rate=rate,
                created_at=datetime.utcnow(),
                response=None
            )

            return await self._review_repo.create_review(review)

        except Exception as e:
            self._logger.error(f"Error creating review: {e}", exc_info=True)
            raise

    async def get_reviews_for_target(
            self,
            target_id: int,
            target_type: ReviewTargetType,
            min_rating: Optional[int] = None,
            max_rating: Optional[int] = None,
            page: int = 1,
            page_size: int = 10
    ) -> list[Review]:
        try:
            offset = (page - 1) * page_size
            return await self._review_repo.get_reviews_for_target(
                target_id,
                target_type,
                min_rating=min_rating,
                max_rating=max_rating
            )
        except Exception as e:
            self._logger.error(f"Error getting reviews for target: {e}", exc_info=True)
            raise

    async def get_review(self, review_id: int) -> Optional[Review]:
        try:
            return await self._review_repo.get_review(review_id)
        except Exception as e:
            self._logger.error(f"Error getting review: {e}", exc_info=True)
            raise

    async def update_review(self, review_id: int, text: str, rate: int) -> Review:
        try:
            review = await self._review_repo.get_review(review_id)
            if not review:
                raise ValueError("Review not found")

            review.text = text
            review.rate = rate
            return await self._review_repo.update_review(review)

        except Exception as e:
            self._logger.error(f"Error updating review: {e}", exc_info=True)
            raise

    async def delete_review(self, review_id: int) -> bool:
        try:
            return await self._review_repo.delete_review(review_id)
        except Exception as e:
            self._logger.error(f"Error deleting review: {e}", exc_info=True)
            raise

    async def respond_to_review(
            self,
            review_id: int,
            responder_id: int,
            response_text: str
    ) -> Review:
        try:
            review = await self._review_repo.get_review(review_id)
            if not review:
                raise ValueError("Review not found")

            if review.target_type == ReviewTargetType.CLINIC:
                clinic = await self._clinic_repo.get_clinic(review.target_id)
                if not clinic:
                    raise ValueError("Clinic not found")
                if clinic.organization_id != responder_id:
                    raise PermissionError("You are not allowed to respond to this review")
            else:
                if review.target_id != responder_id:
                    raise PermissionError("You are not allowed to respond to this review")

            return await self._review_repo.respond_to_review(review_id, response_text)

        except Exception as e:
            self._logger.error(f"Error responding to review: {e}", exc_info=True)
            raise

    async def get_user_reviews(self, user_id: int) -> list[Review]:
        try:
            return await self._review_repo.get_reviews_by_sender(user_id)
        except Exception as e:
            self._logger.error(f"Error getting user reviews: {e}", exc_info=True)
            raise

    async def get_average_rating(
            self,
            target_id: int,
            target_type: ReviewTargetType
    ) -> float:
        try:
            reviews = await self._review_repo.get_reviews_for_target(
                target_id,
                target_type
            )

            if not reviews:
                return 0.0

            total = sum(review.rate for review in reviews)
            return round(total / len(reviews), 1)

        except Exception as e:
            self._logger.error(f"Error calculating average rating: {e}", exc_info=True)
            raise
