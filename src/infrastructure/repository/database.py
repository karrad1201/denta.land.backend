from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv
from sqlalchemy import text


load_dotenv()
POSTGRES_URL = os.getenv('DATABASE_URL')

if "PYTEST_CURRENT_TEST" in os.environ:
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
else:
    DATABASE_URL = POSTGRES_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

Base = declarative_base()

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    from src.infrastructure.repository.schemas.chat_orm import (ChatOrm, MessageOrm, MessageType, TextMessageOrm, FileMessageOrm, ImageMessageOrm, VoiceMessageOrm)
    from src.infrastructure.repository.schemas.clinic_orm import ClinicOrm
    from src.infrastructure.repository.schemas.order_orm import OrderOrm, OrderStatus
    from src.infrastructure.repository.schemas.responses_orm import ResponseOrm
    from src.infrastructure.repository.schemas.review_orm import ReviewOrm
    from src.infrastructure.repository.schemas.user_orm import Role, AdminRoles, UserOrm, SpecialistOrm, PatientOrm, OrganizationOrm, AdminOrm,BlockedUserOrm, AdminRolesEnum
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if "postgresql" in DATABASE_URL:
            result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = result.scalars().all()
            print("Existing tables:", tables)