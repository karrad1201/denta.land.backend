import pytest
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_organization_profile(client: AsyncClient, organization_data: dict):

    # Регистрируем организацию
    org_reg = await client.post("/api/auth/reg", json=organization_data)
    logger.info(f"Organization registration response: {org_reg.status_code}, {org_reg.text}")
    assert org_reg.status_code == 201, f"Organization registration failed: {org_reg.text}"
    org_data = org_reg.json()

    # Логинимся как организация
    login = await client.post("/api/auth/login", json={
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    })
    logger.info(f"Organization login response: {login.status_code}, {login.text}")
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Получаем профиль организации
    response = await client.get("/api/organizations/me", headers=headers)
    logger.info(f"Get organization profile response: {response.status_code}, {response.text}")
    print(response.text)
    assert response.status_code == 200, f"Get organization profile failed: {response.text}"
    profile = response.json()
    assert profile["id"] == org_data["id"]
    assert profile["locations"] == organization_data["locations"]
