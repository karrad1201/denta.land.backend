import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, organization_data: dict):
    # Регистрируем организацию
    org_reg = await client.post("/api/auth/reg", json=organization_data)
    org = org_reg.json()

    # Логинимся как организация
    login = await client.post("/api/auth/login", json={
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Данные в формате OrderCreateRequest
    order_data = {
        "service_type": "Consultation",
        "description": "Need help with back pain",
        "preferred_date": "2023-12-31T12:00:00",
        "patient_id": None,  # Для услуг пациентам
        "clinic_id": None    # Для услуг клиник
    }

    response = await client.post("/api/orders/", json=order_data, headers=headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.text}"

    order = response.json()
    assert order["creator_id"] == org["id"]
    assert order["creator_role"] == "organization"
    assert order["status"] == "active"
    assert "Consultation" in order["specifications"]

@pytest.mark.asyncio
async def test_get_orders(client: AsyncClient, organization_data: dict):
    # Регистрируем организацию
    org_reg = await client.post("/api/auth/reg", json=organization_data)
    logger.info(f"Organization registration response: {org_reg.status_code}, {org_reg.text}")
    assert org_reg.status_code == 201, f"Organization registration failed: {org_reg.text}"
    org = org_reg.json()

    # Логинимся как организация
    login_org = await client.post("/api/auth/login", json={
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    })
    logger.info(f"Organization login response: {login_org.status_code}, {login_org.text}")
    token_org = login_org.json()["access_token"]
    headers_org = {"Authorization": f"Bearer {token_org}"}

    # Создаем заказ
    order_data = {
        "service_type": "Consultation",
        "description": "Need professional help",
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=headers_org)
    logger.info(f"Create order response: {order_resp.status_code}, {order_resp.text}")
    assert order_resp.status_code == 201, f"Create order failed: {order_resp.text}"

    # Получаем заказы организации
    response = await client.get("/api/orders/", headers=headers_org)
    logger.info(f"Get orders response: {response.status_code}, {response.text}")
    assert response.status_code == 200, f"Get orders failed: {response.text}"
    orders = response.json()
    assert len(orders) > 0
    assert orders[0]["creator_id"] == org["id"]

@pytest.mark.asyncio
async def test_update_order_status(client: AsyncClient, organization_data: dict):
    # Регистрируем организацию
    org_reg = await client.post("/api/auth/reg", json=organization_data)
    logger.info(f"Organization registration response: {org_reg.status_code}, {org_reg.text}")
    assert org_reg.status_code == 201, f"Organization registration failed: {org_reg.text}"
    org = org_reg.json()

    # Логинимся как организация
    login_org = await client.post("/api/auth/login", json={
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    })
    logger.info(f"Organization login response: {login_org.status_code}, {login_org.text}")
    token_org = login_org.json()["access_token"]
    headers_org = {"Authorization": f"Bearer {token_org}"}

    # Создаем заказ
    order_data = {
        "service_type": "Consultation",
        "description": "Urgent help needed",
        "preferred_date": (datetime.now() + timedelta(days=1)).isoformat(),
    }
    create_response = await client.post("/api/orders/", json=order_data, headers=headers_org)
    logger.info(f"Create order response: {create_response.status_code}, {create_response.text}")
    assert create_response.status_code == 201, f"Create order failed: {create_response.text}"
    order = create_response.json()

    # Обновляем статус заказа
    response = await client.put(
        f"/api/orders/{order['id']}/status",
        json={"status": "cancelled"},
        headers=headers_org
    )
    logger.info(f"Update order status response: {response.status_code}, {response.text}")
    assert response.status_code == 200, f"Update order status failed: {response.text}"
    assert response.json()["message"] == "Order status updated"

    # Проверяем обновление
    get_response = await client.get(f"/api/orders/{order['id']}", headers=headers_org)
    logger.info(f"Get order response: {get_response.status_code}, {get_response.text}")
    updated_order = get_response.json()
    assert updated_order["status"] == "cancelled"