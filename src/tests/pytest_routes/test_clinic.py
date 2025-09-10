import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from src.infrastructure.repository.schemas.clinic_orm import ClinicOrm

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_create_clinic(client: AsyncClient, organization_data: dict):

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

    # Создаем клинику
    clinic_data = {
        "organization_id": org_data["id"],
        "name": "Test Clinic",
        "location": "Test City",
        "address": "123 Test St",
        "work_hours": {},
        "is_24_7": False
    }
    response = await client.post("/api/clinics/", json=clinic_data, headers=headers)
    logger.info(f"Create clinic response: {response.status_code}, {response.text}")
    assert response.status_code == 201, f"Create clinic failed: {response.text}"
    data = response.json()
    assert data["name"] == "Test Clinic"
    assert data["organization_id"] == org_data["id"]


@pytest.mark.asyncio
async def test_get_clinic(client: AsyncClient, db_session: AsyncSession):
    # Создаем клинику напрямую в БД
    clinic = ClinicOrm(
        organization_id=1,
        name="Test Clinic",
        location="Test City",
        address="123 Test St",
        work_hours={},
        is_24_7=False
    )
    db_session.add(clinic)
    await db_session.commit()

    # Получаем клинику
    response = await client.get(f"/api/clinics/{clinic.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == clinic.id
    assert data["name"] == "Test Clinic"


@pytest.mark.asyncio
async def test_update_clinic(client: AsyncClient, db_session: AsyncSession, organization_data: dict):

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

    # Создаем клинику
    clinic_data = {
        "organization_id": org_data["id"],
        "name": "Test Clinic",
        "location": "Test City",
        "address": "123 Test St",
        "work_hours": {},
        "is_24_7": False
    }
    create_response = await client.post("/api/clinics/", json=clinic_data, headers=headers)
    logger.info(f"Create clinic response: {create_response.status_code}, {create_response.text}")
    assert create_response.status_code == 201, f"Create clinic failed: {create_response.text}"
    clinic = create_response.json()

    # Обновляем клинику
    update_data = {"name": "Updated Clinic", "is_24_7": True}
    response = await client.put(
        f"/api/clinics/{clinic['id']}",
        json=update_data,
        headers=headers
    )
    logger.info(f"Update clinic response: {response.status_code}, {response.text}")
    assert response.status_code == 200, f"Update clinic failed: {response.text}"
    data = response.json()
    assert data["name"] == "Updated Clinic"
    assert data["is_24_7"] is True


@pytest.mark.asyncio
async def test_delete_clinic(client: AsyncClient, db_session: AsyncSession, organization_data: dict):

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

    # Создаем клинику
    clinic_data = {
        "organization_id": org_data["id"],
        "name": "Test Clinic",
        "location": "Test City",
        "address": "123 Test St",
        "work_hours": {},
        "is_24_7": False
    }
    create_response = await client.post("/api/clinics/", json=clinic_data, headers=headers)
    logger.info(f"Create clinic response: {create_response.status_code}, {create_response.text}")
    assert create_response.status_code == 201, f"Create clinic failed: {create_response.text}"
    clinic = create_response.json()

    # Удаляем клинику
    response = await client.delete(
        f"/api/clinics/{clinic['id']}",
        headers=headers
    )
    logger.info(f"Delete clinic response: {response.status_code}, {response.text}")
    assert response.status_code == 204, f"Delete clinic failed: {response.text}"

    # Проверяем, что клиника удалена
    result = await db_session.execute(select(ClinicOrm).where(ClinicOrm.id == clinic['id']))
    clinic_db = result.scalars().first()
    assert clinic_db is None