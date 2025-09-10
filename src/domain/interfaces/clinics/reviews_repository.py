from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entity.clinics.reviews import Review, ReviewTargetType
from typing import Optional, List


class IReviewRepository(ABC):
    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def get_review(self, review_id: int) -> Optional[Review]:
        pass

    @abstractmethod
    async def create_review(self, review: Review) -> Review:
        pass

    @abstractmethod
    async def update_review(self, review: Review) -> Review:
        pass

    @abstractmethod
    async def delete_review(self, review_id: int) -> bool:
        pass

    @abstractmethod
    async def respond_to_review(self, review_id: int, response: str) -> Review:
        pass

    @abstractmethod
    async def get_reviews_for_target(
            self,
            target_id: int,
            target_type: ReviewTargetType,
            *,
            min_rating: Optional[int] = None,
            max_rating: Optional[int] = None
    ) -> List[Review]:
        pass

    @abstractmethod
    async def get_reviews_by_sender(self, sender_id: int) -> List[Review]:
        pass

    @abstractmethod
    async def get_reviews_for_order(self, order_id: int) -> List[Review]:
        pass

    @abstractmethod
    async def has_review_for_order(
            self,
            order_id: int,
            sender_id: int,
            target_id: int
    ) -> bool:
        pass
