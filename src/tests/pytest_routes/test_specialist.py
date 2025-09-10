import pytest
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_specialist_profile(client: AsyncClient, specialist_data: dict):
    # Регистрируем специалиста
    specialist_reg = await client.post("/api/auth/reg", json=specialist_data)
    logger.info(f"Specialist registration response: {specialist_reg.status_code}, {specialist_reg.text}")
    assert specialist_reg.status_code == 201, f"Specialist registration failed: {specialist_reg.text}"
    specialist = specialist_reg.json()

    # Логинимся как специалист
    login = await client.post("/api/auth/login", json={
        "nickname": specialist_data["nickname"],
        "password": specialist_data["password"]
    })
    logger.info(f"Specialist login response: {login.status_code}, {login.text}")
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Получаем профиль специалиста
    response = await client.get("/api/specialists/me", headers=headers)
    logger.info(f"Get specialist profile response: {response.status_code}, {response.text}")
    assert response.status_code == 200, f"Get specialist profile failed: {response.text}"
    profile = response.json()
    assert profile["id"] == specialist["id"]
    assert profile["qualification"] == specialist_data["qualification"]
