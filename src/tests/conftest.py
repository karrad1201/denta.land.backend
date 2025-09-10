import sys
import os
import uuid

import pytest
import pytest_asyncio  # Добавляем импорт
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import ASGITransport

# Добавляем корень проекта в PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

# Теперь импортируем после добавления пути
from src.main import app
from src.infrastructure.repository.database import Base
from src.infrastructure.repository.schemas.user_orm import (
        UserOrm, SpecialistOrm, PatientOrm, OrganizationOrm, AdminOrm, BlockedUserOrm
    )


# Тестовая БД в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
def set_rate_limiter_env(monkeypatch):
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "true")
    yield


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    from src.infrastructure.repository.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()




@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    async with async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession
    )() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session) -> AsyncClient:
    from src.dependencies import get_db
    from src.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as client:
        yield client

# Фикстуры с тестовыми данными
@pytest.fixture
def patient_data():
    return {
        "nickname": f"test_patient_{uuid.uuid4().hex[:6]}",
        "name": "Test Patient",
        "password": "SecurePass123!",
        "country": "Testland",
        "city": "Test City",
        "email": f"patient_{uuid.uuid4().hex[:6]}@test.com",
        "role": "patient",
        "phone_number": "+1234567890"
    }

@pytest.fixture
def specialist_data():
    return {
        "nickname": f"test_spec_{uuid.uuid4().hex[:6]}",
        "name": "Test Specialist",
        "password": "SecurePass123!",
        "country": "Testland",
        "specifications": ["Cardiology", "Surgery"],
        "qualification": "MD",
        "experience_years": 5,
        "email": f"specialist_{uuid.uuid4().hex[:6]}@test.com",
        "role": "specialist",
        "phone_number": "+1234567890"
    }

@pytest.fixture
def organization_data():
    return {
        "nickname": f"test_org_{uuid.uuid4().hex[:6]}",
        "name": "Test Organn",
        "password": "SecurePass123!",
        "country": "Testland",
        "locations": ["Location 1", "Location 2"],
        "email": f"organization_{uuid.uuid4().hex[:6]}@test.com",
        "role": "organization",
        "phone_number": "+1234567890"
    }

@pytest.fixture
def admin_data():
    from src.domain.entity.users.admin.admin_entity import AdminRoles
    return {
        "nickname": f"test_ad_{uuid.uuid4().hex[:6]}",
        "name": "Test Admin",
        "password": "SecurePass123!",
        "country": "Testland",
        "admin_role": AdminRoles.ADMINISTRATOR.value,
        "is_superadmin": True,
        "email": f"admin_{uuid.uuid4().hex[::6]}@test.com",
        "role": "admin",
        "phone_number": "+1234567890"
    }


@pytest_asyncio.fixture
async def first_admin(db_session: AsyncSession):
    from src.infrastructure.services.registration.hash_password import hash_password
    from src.infrastructure.repository.schemas.user_orm import UserOrm, AdminOrm
    from src.domain.entity.users.user import Role
    from src.domain.entity.users.admin.admin_entity import AdminRoles
    from os import getenv
    from dotenv import load_dotenv
    load_dotenv()

    hashed_password = await hash_password("adminpassword")

    admin_user = UserOrm(
        nickname=f"test_{uuid.uuid4().hex[:6]}",
        name="First Admin",
        password_hash=hashed_password,
        role=Role.ADMIN.value,
        country="Testland",
        email=f"admin_{uuid.uuid4().hex[::6]}@test.com",
        phone_number="+1234567890"
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    admin_profile = AdminOrm(
        user_id=admin_user.id,
        admin_role=AdminRoles.ADMINISTRATOR.value,
        is_superadmin=True
    )
    db_session.add(admin_profile)
    await db_session.commit()


    import jwt
    from datetime import datetime, timedelta
    JWT_SECRET = getenv('JWT_SECRET_KEY')
    JWT_ALGORITHM = getenv('JWT_ALGORITHM')
    expiration = datetime.utcnow() + timedelta(days=1)
    payload = {
        "sub": str(admin_user.id),
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "user": admin_user,
        "admin": admin_profile,
        "token": token
    }