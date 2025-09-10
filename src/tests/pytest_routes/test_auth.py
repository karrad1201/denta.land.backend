import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from src.domain.entity.users.user import Role
from src.infrastructure.repository.schemas.user_orm import UserOrm

logger = logging.getLogger(__name__)


# Тесты для регистрации
@pytest.mark.asyncio
async def test_register_patient(client: AsyncClient, patient_data: dict):
    patient_data["nickname"] = "test_patient"

    response = await client.post("/api/auth/reg", json=patient_data)
    logger.info(f"Register patient response: {response.status_code}, {response.text}")

    assert response.status_code == 201, f"Registration failed: {response.text}"
    data = response.json()

    # Проверка общих полей
    print(data)
    assert data["nickname"] == patient_data["nickname"]
    assert data["name"] == patient_data["name"]
    assert data["role"] == Role.PATIENT.value

    # Проверка специфичных полей
    assert data["city"] == patient_data["city"]
    assert "password" not in data  # Пароль не должен возвращаться


@pytest.mark.asyncio
async def test_register_specialist(client: AsyncClient, specialist_data: dict):
    response = await client.post("/api/auth/reg", json=specialist_data)

    assert response.status_code == 201
    data = response.json()

    assert data["nickname"] == specialist_data["nickname"]
    assert data["role"] == Role.SPECIALIST.value
    assert data["specifications"] == specialist_data["specifications"]
    assert data["qualification"] == specialist_data["qualification"]
    assert data["experience_years"] == specialist_data["experience_years"]


@pytest.mark.asyncio
async def test_register_organization(client: AsyncClient, organization_data: dict):
    response = await client.post("/api/auth/reg", json=organization_data)

    assert response.status_code == 201
    data = response.json()

    assert data["nickname"] == organization_data["nickname"]
    assert data["role"] == Role.ORGANIZATION.value
    assert data["locations"] == organization_data["locations"]
    assert data["clinics"] == []  # Должен быть пустой список по умолчанию
    assert data["members"] == []  # Должен быть пустой список по умолчанию


@pytest.mark.asyncio
async def test_register_admin(client: AsyncClient, admin_data: dict, first_admin: dict):
    headers = {"Authorization": f"Bearer {first_admin['token']}"}

    response = await client.post("/api/auth/reg", json=admin_data, headers=headers)

    assert response.status_code == 201
    data = response.json()

    assert data["nickname"] == admin_data["nickname"]
    assert data["role"] == Role.ADMIN.value
    assert data["admin_role"] == admin_data["admin_role"]
    assert data["is_superadmin"] == admin_data["is_superadmin"]


# Тесты для обработки ошибок
@pytest.mark.asyncio
async def test_duplicate_nickname(client: AsyncClient, patient_data: dict):
    # Первая регистрация - успешна
    response1 = await client.post("/api/auth/reg", json=patient_data)
    assert response1.status_code == 201

    # Вторая регистрация с тем же nickname
    duplicate_data = patient_data.copy()
    duplicate_data["email"] = "nesdw@example.com"  # Меняем email, но nickname тот же
    response2 = await client.post("/api/auth/reg", json=duplicate_data)

    assert response2.status_code == 400
    assert "Nickname already exists" in response2.text


@pytest.mark.asyncio
async def test_invalid_data(client: AsyncClient):
    response = await client.post("/api/auth/reg", json={
        "nickname": "inv",
        "name": "I"
    })

    assert response.status_code == 422
    errors = response.json()["detail"]

    error_messages = [e["msg"] for e in errors]
    assert any("field required" in msg.lower() for msg in error_messages)


@pytest.mark.asyncio
async def test_role_specific_validation(client: AsyncClient):
    # Для организации без locations
    response = await client.post("/api/auth/reg", json={
        "nickname": "org_no_locations",
        "name": "Invalid Org",
        "password": "Pass123!",
        "country": "Testland",
        "role": Role.ORGANIZATION.value,
        "email": "patient1@test.com"
    })

    assert response.status_code == 422
    assert "locations" in response.text


# Тест для проверки безопасности
@pytest.mark.asyncio
async def test_password_hashing(
        client: AsyncClient,
        patient_data: dict,
        db_session: AsyncSession
):
    response = await client.post("/api/auth/reg", json=patient_data)
    assert response.status_code == 201

    # Проверяем, что пароль захэширован в БД
    result = await db_session.execute(
        select(UserOrm).where(UserOrm.nickname == patient_data["nickname"])
    )
    user = result.scalars().first()

    assert user is not None
    assert user.password_hash != patient_data["password"]
    assert user.password_hash.startswith("$2b$")  # Проверка формата bcrypt




@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    register_data = {
        "nickname": "login_patient",
        "name": "Login Patient",
        "password": "Pass123!",
        "country": "Testland",
        "city": "Login City",
        "role": "patient",
        "email": "login_patient@test.com",
        "phone_number": "+1234567890"
    }

    response_register = await client.post("/api/auth/reg", json=register_data)
    print("Register response:", response_register.status_code, response_register.json())  # 🛠️ Отладка
    assert response_register.status_code == 201, f"Registration failed: {response_register.json()}"

    login_data = {
        "nickname": register_data["nickname"],
        "password": register_data["password"]
    }

    response_login = await client.post("/api/auth/login", json=login_data)
    print("Login response:", response_login.status_code, response_login.json())  # 🛠️ Отладка
    assert response_login.status_code == 200, f"Login failed: {response_login.json()}"

    data = response_login.json()
    assert data["user"]["nickname"] == register_data["nickname"]
    assert data["user"]["role"] == Role.PATIENT.value
    assert data["access_token"]




