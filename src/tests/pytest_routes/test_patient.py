import pytest
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)



@pytest.mark.asyncio
async def test_patient_profile(client: AsyncClient, patient_data: dict):

    # Регистрируем пациента
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    logger.info(f"Patient registration response: {patient_reg.status_code}, {patient_reg.text}")
    assert patient_reg.status_code == 201, f"Patient registration failed: {patient_reg.text}"
    patient = patient_reg.json()

    # Логинимся как пациент
    login = await client.post("/api/auth/login", json={
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    })
    logger.info(f"Patient login response: {login.status_code}, {login.text}")
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Получаем профиль пациента
    response = await client.get("/api/patients/me", headers=headers)
    logger.info(f"Get patient profile response: {response.status_code}, {response.text}")
    assert response.status_code == 200, f"Get patient profile failed: {response.text}"
    profile = response.json()
    assert profile["id"] == patient["id"]
    assert profile["city"] == patient_data["city"]

    # Обновляем профиль
    update_data = {"city": "New City"}
    response = await client.put("/api/patients/me", json=update_data, headers=headers)
    logger.info(f"Update patient profile response: {response.status_code}, {response.text}")
    assert response.status_code == 200, f"Update patient profile failed: {response.text}"
    updated_profile = response.json()
    assert updated_profile["city"] == "New City"