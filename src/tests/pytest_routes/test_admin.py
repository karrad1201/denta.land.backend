import pytest
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_admin_actions(client: AsyncClient, admin_data: dict, patient_data: dict, first_admin: dict):
    logger.info("--- Starting test_admin_actions ---")

    headers = {"Authorization": f"Bearer {first_admin['token']}"}

    # Шаг 1: Регистрация админа (с токеном)
    logger.info("Step 1: Registering admin...")
    admin_reg = await client.post("/api/auth/reg", json=admin_data, headers=headers)
    logger.info(f"Admin registration response: Status={admin_reg.status_code}, Body={admin_reg.text}")
    assert admin_reg.status_code == 201, f"Admin registration failed: {admin_reg.text}"
    admin = admin_reg.json()
    logger.info(f"Admin registered successfully with ID: {admin.get('id')}")

    # Шаг 2: Логин админа
    logger.info("Step 2: Logging in as admin...")
    login = await client.post("/api/auth/login", json={
        "nickname": admin_data["nickname"],
        "password": admin_data["password"]
    })
    logger.info(f"Admin login response: Status={login.status_code}, Body={login.text}")
    assert login.status_code == 200, f"Admin login failed: {login.text}"
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    logger.info("Admin logged in successfully.")

    # Шаг 3: Регистрация пациента
    logger.info("Step 3: Registering patient...")
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    logger.info(f"Patient registration response: Status={patient_reg.status_code}, Body={patient_reg.text}")
    assert patient_reg.status_code == 201, f"Patient registration failed: {patient_reg.text}"
    patient = patient_reg.json()
    logger.info(f"Patient registered successfully with ID: {patient.get('id')}")

    # Шаг 4: Получение всех пользователей
    logger.info("Step 4: Getting all users...")
    response = await client.get("/api/admin/users", headers=headers)
    logger.info(f"Get users response: Status={response.status_code}, Body={response.text}")
    print(response.text)
    assert response.status_code == 200, f"Get users failed: {response.text}"
    users = response.json()
    assert len(users) >= 2, "Expected at least 2 users (admin and patient)."
    logger.info(f"Successfully retrieved {len(users)} users.")

    # Шаг 5: Блокировка пользователя
    logger.info("Step 5: Blocking a user...")
    block_data = {
        "user_id": patient["id"],
        "action": "block",
        "reason": "Test block"
    }
    response = await client.post("/api/admin/user-actions", json=block_data, headers=headers)
    logger.info(f"Block user response: Status={response.status_code}, Body={response.text}")
    assert response.status_code == 200, f"Block user failed: {response.text}"
    assert "block" in response.json()["message"], "Block message not found in response."
    logger.info(f"User {patient.get('id')} blocked successfully.")

    logger.info("Step 6: Getting statistics...")
    response = await client.get("/api/admin/statistics", headers=headers)
    logger.info(f"Get statistics response: Status={response.status_code}, Body={response.text}")

    # Проверяем, что запрос прошел успешно
    assert response.status_code == 200, f"Get statistics failed: {response.text}"
    stats = response.json()

    # Проверяем наличие всех необходимых полей в ответе
    expected_fields = ["total_users", "patients", "specialists", "organizations", "admins"]
    for field in expected_fields:
        assert field in stats, f"Field '{field}' not found in statistics response."

    # Проверяем, что количество пользователей соответствует ожиданиям (минимум 2)
    assert stats["total_users"] > 0, "Total users count should be greater than 0."
    assert stats["patients"] >= 1, "Patients count should be at least 1."
    assert stats["admins"] >= 1, "Admins count should be at least 1."

    logger.info("Successfully retrieved and validated statistics.")

    logger.info("--- Test test_admin_actions finished successfully ---")