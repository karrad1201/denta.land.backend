import pytest
from httpx import AsyncClient
import logging
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'test-secret')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')


# Генерация истекшего токена для тестов
def generate_expired_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() - timedelta(minutes=10)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Тест обновления базовых данных
@pytest.mark.asyncio
async def test_update_basic_settings(client: AsyncClient, patient_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=patient_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Логин
    login_data = {
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Обновление настроек
    update_data = {
        "name": "Updated Name",
        "country": "Updated Country",
        "email": "updated@example.com"
    }
    response = await client.put(
        "/api/settings",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Проверка изменений
    user_response = await client.get(f"/api/user/{user_id}")
    user_data = user_response.json()
    print(user_data)
    assert user_data["name"] == "Updated Name"
    assert user_data["country"] == "Updated Country"
    assert user_data["email"] == "updated@example.com"


# Тест обновления пароля
@pytest.mark.asyncio
async def test_update_password(client: AsyncClient, patient_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=patient_data)
    assert response.status_code == 201
    user = response.json()

    # Логин
    login_data = {
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Обновление пароля
    new_password = "new_strong_password_123!"
    response = await client.put(
        "/api/settings",
        json={"password": new_password},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Попытка входа со старым паролем
    old_login_response = await client.post("/api/auth/login", json=login_data)
    assert old_login_response.status_code == 400

    # Вход с новым паролем
    new_login_data = {
        "nickname": patient_data["nickname"],
        "password": new_password
    }
    new_login_response = await client.post("/api/auth/login", json=new_login_data)
    assert new_login_response.status_code == 200


# Тест обновления ролевых данных (пациент)
@pytest.mark.asyncio
async def test_update_patient_settings(client: AsyncClient, patient_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=patient_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Логин
    login_data = {
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Обновление города
    response = await client.put(
        "/api/settings",
        json={"city": "New York"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Проверка изменений
    user_response = await client.get(f"/api/patients/{user_id}")
    print(user_response.json())
    assert user_response.json()["city"] == "New York"


# Тест обновления ролевых данных (специалист)
@pytest.mark.asyncio
async def test_update_specialist_settings(client: AsyncClient, specialist_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=specialist_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Логин
    login_data = {
        "nickname": specialist_data["nickname"],
        "password": specialist_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Обновление специализаций и квалификации
    update_data = {
        "specifications": ["Cardiology", "Neurology"],
        "qualification": "PhD"
    }
    response = await client.put(
        "/api/settings",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Проверка изменений
    user_response = await client.get(f"/api/specialists/{user_id}")
    user_data = user_response.json()
    print(user_data)
    assert set(user_data["specifications"]) == set(["Cardiology", "Neurology"])
    assert user_data["qualification"] == "PhD"


# Тест обновления ролевых данных (организация)
@pytest.mark.asyncio
async def test_update_organization_settings(client: AsyncClient, organization_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=organization_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Логин
    login_data = {
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Обновление локаций
    new_locations = ["New York", "Los Angeles"]
    response = await client.put(
        "/api/settings",
        json={"locations": new_locations},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Проверка изменений
    user_response = await client.get(f"/api/organizations/{user_id}")
    assert set(user_response.json()["locations"]) == set(new_locations)


@pytest.mark.asyncio
async def test_update_admin_settings(client: AsyncClient, admin_data: dict, first_admin: dict):
    headers = {"Authorization": f"Bearer {first_admin['token']}"}

    # Регистрация нового администратора
    admin_data["admin_role"] = "administrator"
    admin_data["is_superadmin"] = False
    response = await client.post("/api/auth/reg", json=admin_data, headers=headers)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Логин
    login_data = {
        "nickname": admin_data["nickname"],
        "password": admin_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Обновление роли и статуса
    update_data = {
        "admin_role": "administrator",
        "is_superadmin": True
    }
    response = await client.put(
        "/api/settings",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Проверка изменений
    user_response = await client.get(f"/api/admin/{user_id}", headers={"Authorization": f"Bearer {token}"})
    user_data = user_response.json()
    print(user_data)
    assert user_data["admin_role"] == "administrator"
    assert user_data["is_superadmin"] is True


# Тест на ошибку: дубликат email
@pytest.mark.asyncio
async def test_duplicate_email_error(client: AsyncClient, patient_data: dict, specialist_data: dict):
    # Регистрация первого пользователя
    response1 = await client.post("/api/auth/reg", json=patient_data)
    assert response1.status_code == 201

    # Регистрация второго пользователя
    response2 = await client.post("/api/auth/reg", json=specialist_data)
    assert response2.status_code == 201

    # Логин первым пользователем
    login_data = {
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Попытка обновить email на существующий
    response = await client.put(
        "/api/settings",
        json={"email": specialist_data["email"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Email already exists" in response.text


# Тест на ошибку: дубликат nickname
@pytest.mark.asyncio
async def test_duplicate_nickname_error(client: AsyncClient, patient_data: dict, specialist_data: dict):
    # Регистрация первого пользователя
    response1 = await client.post("/api/auth/reg", json=patient_data)
    assert response1.status_code == 201

    # Регистрация второго пользователя
    response2 = await client.post("/api/auth/reg", json=specialist_data)
    assert response2.status_code == 201

    # Логин первым пользователем
    login_data = {
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Попытка обновить nickname на существующий
    response = await client.put(
        "/api/settings",
        json={"nickname": specialist_data["nickname"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Nickname already exists" in response.text


# Тест на ошибку: неверный токен
@pytest.mark.asyncio
async def test_invalid_token_error(client: AsyncClient, patient_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=patient_data)
    assert response.status_code == 201


    response = await client.put(
        "/api/settings",
        json={"city": "New York"},
        headers={"Authorization": f"Bearer test_token"}
    )
    assert (
            "Not enough segments" in response.text
            or "Invalid token" in response.text
            or "Invalid crypto padding" in response.text
    )


# Тест на ошибку: истекший токен
@pytest.mark.asyncio
async def test_expired_token_error(client: AsyncClient, patient_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=patient_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Генерация истекшего токена
    expired_token = generate_expired_token(user_id)

    # Попытка обновления с истекшим токеном
    response = await client.put(
        "/api/settings",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    print(response.text)
    assert response.status_code == 400
    assert "Signature has expired" in response.text


# Тест на ошибку: неавторизованный доступ
@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.put(
        "/api/settings",
        json={"name": "New Name"}
    )
    print(response.text)
    assert response.status_code in (401, 402, 422)
    assert "Field required" in response.text


# Тест на ошибку: неверный формат токена
@pytest.mark.asyncio
async def test_invalid_auth_scheme(client: AsyncClient, patient_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=patient_data)
    assert response.status_code == 201

    # Логин
    login_data = {
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Неверный формат заголовка
    response = await client.put(
        "/api/settings",
        json={"name": "New Name"},
        headers={"Authorization": token}  # Пропущен "Bearer"
    )
    assert response.status_code == 401
    assert "Invalid authentication scheme" in response.text


# Тест комплексного обновления
@pytest.mark.asyncio
async def test_complex_update(client: AsyncClient, patient_data: dict):
    # Регистрация
    response = await client.post("/api/auth/reg", json=patient_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Логин
    login_data = {
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    }
    login_response = await client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Комплексное обновление
    update_data = {
        "name": "New Full Name",
        "email": "new.email@example.com",
        "city": "Berlin",
        "password": "new_strong_password_123!"
    }
    response = await client.put(
        "/api/settings",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Проверка изменений
    user_response = await client.get(f"/api/patients/{user_id}")
    user_data = user_response.json()
    print(user_data)
    assert user_data["name"] == "New Full Name"
    assert user_data["email"] == "new.email@example.com"
    assert user_data["city"] == "Berlin"

    # Проверка нового пароля
    new_login_data = {
        "nickname": patient_data["nickname"],
        "password": "new_strong_password_123!"
    }
    new_login_response = await client.post("/api/auth/login", json=new_login_data)
    assert new_login_response.status_code == 200