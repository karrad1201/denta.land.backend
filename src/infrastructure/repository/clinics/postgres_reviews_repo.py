from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.domain.entity.clinics.reviews import Review, ReviewTargetType
from src.domain.interfaces.clinics.reviews_repository import IReviewRepository
from src.infrastructure.adapters.orm_entity_adapter import ReviewOrmEntityAdapter
from src.infrastructure.repository.schemas.review_orm import ReviewOrm
import logging
from typing import List, Optional


class PostgresReviewRepo(IReviewRepository):
    def __init__(self, session: AsyncSession, adapter: ReviewOrmEntityAdapter):
        self._session = session
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def get_review(self, review_id: int) -> Optional[Review]:
        try:
            result = await self._session.execute(
                select(ReviewOrm).where(ReviewOrm.id == review_id)
            )
            review_orm = result.scalar_one_or_none()
            if review_orm:
                return await self._adapter.to_entity(review_orm)
            return None
        except Exception as e:
            self._logger.error(f"Error getting review: {e}", exc_info=True)
            raise

    async def create_review(self, review: Review) -> Review:
        try:
            review_orm = await self._adapter.to_orm(review)
            self._session.add(review_orm)
            await self._session.commit()
            await self._session.refresh(review_orm)
            return await self._adapter.to_entity(review_orm)
        except Exception as e:
            self._logger.error(f"Error creating review: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def update_review(self, review: Review) -> Review:
        try:
            review_orm = await self._adapter.to_orm(review)
            merged_orm = await self._session.merge(review_orm)
            await self._session.commit()
            return await self._adapter.to_entity(merged_orm)
        except Exception as e:
            self._logger.error(f"Error updating review: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def delete_review(self, review_id: int) -> bool:
        try:
            result = await self._session.execute(
                select(ReviewOrm).where(ReviewOrm.id == review_id)
            )
            review_orm = result.scalar_one_or_none()
            if review_orm:
                await self._session.delete(review_orm)
                await self._session.commit()
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error deleting review: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def respond_to_review(self, review_id: int, response: str) -> Review:
        try:
            result = await self._session.execute(
                select(ReviewOrm).where(ReviewOrm.id == review_id)
            )
            review_orm = result.scalar_one_or_none()
            if review_orm:
                review_orm.response = response
                await self._session.commit()
                await self._session.refresh(review_orm)
                return await self._adapter.to_entity(review_orm)
            raise ValueError("Review not found")
        except Exception as e:
            self._logger.error(f"Error responding to review: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def get_reviews_for_target(
            self,
            target_id: int,
            target_type: ReviewTargetType,
            *,
            min_rating: Optional[int] = None,
            max_rating: Optional[int] = None
    ) -> List[Review]:
        try:
            query = select(ReviewOrm).where(
                and_(
                    ReviewOrm.target_id == target_id,
                    ReviewOrm.target_type == target_type.value
                )
            )

            if min_rating is not None:
                query = query.where(ReviewOrm.rate >= min_rating)

            if max_rating is not None:
                query = query.where(ReviewOrm.rate <= max_rating)

            result = await self._session.execute(query)
            reviews_orm = result.scalars().all()
            return [await self._adapter.to_entity(review) for review in reviews_orm]
        except Exception as e:
            self._logger.error(f"Error getting reviews for target: {e}", exc_info=True)
            raise

    async def get_reviews_by_sender(self, sender_id: int) -> List[Review]:
        try:
            result = await self._session.execute(
                select(ReviewOrm).where(ReviewOrm.sender_id == sender_id)
            )
            reviews_orm = result.scalars().all()
            return [await self._adapter.to_entity(review) for review in reviews_orm]
        except Exception as e:
            self._logger.error(f"Error getting reviews by sender: {e}", exc_info=True)
            raise

    async def get_reviews_for_order(self, order_id: int) -> List[Review]:
        try:
            result = await self._session.execute(
                select(ReviewOrm).where(ReviewOrm.order_id == order_id)
            )
            reviews_orm = result.scalars().all()
            return [await self._adapter.to_entity(review) for review in reviews_orm]
        except Exception as e:
            self._logger.error(f"Error getting reviews for order: {e}", exc_info=True)
            raise

    async def has_review_for_order(
            self,
            order_id: int,
            sender_id: int,
            target_id: int
    ) -> bool:
        try:
            result = await self._session.execute(
                select(ReviewOrm).where(
                    and_(
                        ReviewOrm.order_id == order_id,
                        ReviewOrm.sender_id == sender_id,
                        ReviewOrm.target_id == target_id
                    )
                )
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            self._logger.error(f"Error checking review existence: {e}", exc_info=True)
            raise
