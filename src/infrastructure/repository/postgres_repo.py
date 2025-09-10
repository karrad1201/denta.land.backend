from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic

T = TypeVar('T')


class PostgresRepo(Generic[T]):
    def __init__(self, session: AsyncSession):
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session
