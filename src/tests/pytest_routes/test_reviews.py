import pytest
from httpx import AsyncClient
import logging
from datetime import datetime, timedelta
from src.domain.entity.users.user import Role
from src.domain.entity.orders.order import OrderStatus
import uuid

logger = logging.getLogger(__name__)


def generate_specialist_data():
    unique_id = uuid.uuid4().hex[:8]
    return {
        "nickname": f"test_spec_{unique_id}",
        "name": f"Test Specialist {unique_id}",
        "password": "SecurePass123!",
        "country": "Testland",
        "specifications": ["Cardiology", "Surgery"],
        "qualification": "MD",
        "experience_years": 5,
        "email": f"specialist_{unique_id}@test.com",
        "role": "specialist",
        "phone_number": f"+123456{unique_id[:6]}"
    }


@pytest.mark.asyncio
async def test_create_review_for_clinic(
        client: AsyncClient,
        patient_data: dict,
        organization_data: dict,
        specialist_data: dict
):
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
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Регистрируем организацию
    org_reg = await client.post("/api/auth/reg", json=organization_data)
    logger.info(f"Organization registration response: {org_reg.status_code}, {org_reg.text}")
    assert org_reg.status_code == 201, f"Organization registration failed: {org_reg.text}"
    org = org_reg.json()

    # Логинимся как организация
    org_login = await client.post("/api/auth/login", json={
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    })
    org_token = org_login.json()["access_token"]
    org_headers = {"Authorization": f"Bearer {org_token}"}

    # Создаем клинику (с авторизацией организации)
    clinic_data = {
        "organization_id": org["id"],
        "name": "Test Clinic",
        "location": "Test City",
        "address": "123 Test St"
    }
    clinic_resp = await client.post("/api/clinics/", json=clinic_data, headers=org_headers)
    logger.info(f"Create clinic response: {clinic_resp.status_code}, {clinic_resp.text}")
    assert clinic_resp.status_code == 201, f"Create clinic failed: {clinic_resp.text}"
    clinic = clinic_resp.json()

    # Регистрируем специалиста
    specialist_reg = await client.post("/api/auth/reg", json=specialist_data)
    logger.info(f"Specialist registration response: {specialist_reg.status_code}, {specialist_reg.text}")
    assert specialist_reg.status_code == 201, f"Specialist registration failed: {specialist_reg.text}"
    specialist = specialist_reg.json()

    # Создаем заказ от имени специалиста
    spec_login = await client.post("/api/auth/login", json={
        "nickname": specialist_data["nickname"],
        "password": specialist_data["password"]
    })
    spec_token = spec_login.json()["access_token"]
    spec_headers = {"Authorization": f"Bearer {spec_token}"}

    order_data = {
        "service_type": "Consultation",
        "description": "Need help with back pain",
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=spec_headers)
    logger.info(f"Create order response: {order_resp.status_code}, {order_resp.text}")
    assert order_resp.status_code == 201, f"Create order failed: {order_resp.text}"
    order = order_resp.json()

    # Обновляем статус заказа на "completed" (от имени специалиста)
    status_update = await client.put(
        f"/api/orders/{order['id']}/status",
        json={"status": OrderStatus.COMPLETED.value},
        headers=spec_headers
    )
    logger.info(f"Update order status response: {status_update.status_code}, {status_update.text}")
    assert status_update.status_code == 200, f"Update order status failed: {status_update.text}"

    # Создаем отзыв на клинику (от имени пациента)
    review_data = {
        "order_id": order["id"],
        "target_id": clinic["id"],
        "target_type": "clinic",
        "text": "Great service and facilities!",
        "rate": 9
    }
    response = await client.post("/api/reviews/", json=review_data, headers=headers)
    logger.info(f"Create review response: {response.status_code}, {response.text}")
    assert response.status_code == 201, f"Create review failed: {response.text}"

    review = response.json()
    assert review["order_id"] == order["id"]
    assert review["target_id"] == clinic["id"]
    assert review["target_type"] == "clinic"
    assert review["rate"] == 9


@pytest.mark.asyncio
async def test_create_review_for_specialist(
        client: AsyncClient,
        patient_data: dict,
        specialist_data: dict
):
    # Регистрируем пациента
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    patient = patient_reg.json()

    # Логинимся как пациент
    login = await client.post("/api/auth/login", json={
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Регистрируем специалиста
    specialist_reg = await client.post("/api/auth/reg", json=specialist_data)
    specialist = specialist_reg.json()

    # Создаем заказ от имени специалиста
    spec_login = await client.post("/api/auth/login", json={
        "nickname": specialist_data["nickname"],
        "password": specialist_data["password"]
    })
    spec_token = spec_login.json()["access_token"]
    spec_headers = {"Authorization": f"Bearer {spec_token}"}

    order_data = {
        "service_type": "Consultation",
        "description": "Need help with back pain",
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=spec_headers)
    order = order_resp.json()

    # Обновляем статус заказа на "completed" (от имени специалиста)
    await client.put(
        f"/api/orders/{order['id']}/status",
        json={"status": OrderStatus.COMPLETED.value},
        headers=spec_headers
    )

    # Создаем отзыв на специалиста (от имени пациента)
    review_data = {
        "order_id": order["id"],
        "target_id": specialist["id"],
        "target_type": "specialist",
        "text": "Excellent consultation!",
        "rate": 10
    }
    response = await client.post("/api/reviews/", json=review_data, headers=headers)
    print(response.json())
    assert response.status_code == 201

    review = response.json()
    assert review["target_id"] == specialist["id"]
    assert review["target_type"] == "specialist"


@pytest.mark.asyncio
async def test_respond_to_review(
        client: AsyncClient,
        specialist_data: dict,
        organization_data: dict
):
    # Регистрируем пациента (используем данные специалиста для пациента)
    patient_reg = await client.post("/api/auth/reg", json=specialist_data)
    patient = patient_reg.json()

    # Логинимся как пациент
    login = await client.post("/api/auth/login", json={
        "nickname": specialist_data["nickname"],
        "password": specialist_data["password"]
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Регистрируем организацию
    org_reg = await client.post("/api/auth/reg", json=organization_data)
    org = org_reg.json()

    # Логинимся как организация
    org_login = await client.post("/api/auth/login", json={
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    })
    org_token = org_login.json()["access_token"]
    org_headers = {"Authorization": f"Bearer {org_token}"}

    # Создаем клинику от имени организации
    clinic_data = {
        "organization_id": org["id"],
        "name": "Test Clinic",
        "location": "Test City",
        "address": "123 Test St"
    }
    clinic_resp = await client.post("/api/clinics/", json=clinic_data, headers=org_headers)
    clinic = clinic_resp.json()

    # Создаем специалиста для создания заказа
    creator_spec_data = generate_specialist_data()
    creator_reg = await client.post("/api/auth/reg", json=creator_spec_data)
    creator = creator_reg.json()

    # Логинимся как специалист для создания заказа
    creator_login = await client.post("/api/auth/login", json={
        "nickname": creator_spec_data["nickname"],
        "password": creator_spec_data["password"]
    })
    creator_token = creator_login.json()["access_token"]
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # Создаем заказ от имени организации
    order_data = {
        "service_type": "Consultation",
        "description": "Need help with back pain",
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=org_headers)
    order = order_resp.json()

    # Обновляем статус заказа на "completed" (от имени специалиста)
    status_resp = await client.put(
        f"/api/orders/{order['id']}/status",
        json={"status": OrderStatus.COMPLETED.value},
        headers=org_headers
    )
    assert status_resp.status_code == 200

    # Проверяем, что статус действительно изменился
    updated_order = await client.get(f"/api/orders/{order['id']}", headers=org_headers)
    assert updated_order.json()["status"] == OrderStatus.COMPLETED.value
    print("Order after status change:", updated_order.json())

    # Создаем отзыв от имени пациента
    review_data = {
        "order_id": order["id"],
        "target_id": clinic["id"],
        "target_type": "clinic",
        "text": "Great service!",
        "rate": 8
    }
    review_resp = await client.post("/api/reviews/", json=review_data, headers=headers)
    print("Review creation response:", review_resp.json())
    assert review_resp.status_code == 201  # Проверяем успешное создание

    review = review_resp.json()
    assert "id" in review  # Проверяем наличие ID

    # Организация отвечает на отзыв
    response_data = {"response": "Thank you for your feedback!"}
    response = await client.post(
        f"/api/reviews/{review['id']}/respond",
        json=response_data,
        headers=org_headers
    )
    assert response.status_code == 200

    updated_review = response.json()
    assert updated_review["response"] == "Thank you for your feedback!"


@pytest.mark.asyncio
async def test_get_reviews_for_target(
        client: AsyncClient,
        patient_data: dict,
        organization_data: dict
):
    # Регистрируем пациента
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    patient = patient_reg.json()

    # Логинимся как пациент
    login = await client.post("/api/auth/login", json={
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Регистрируем организацию
    org_reg = await client.post("/api/auth/reg", json=organization_data)
    org = org_reg.json()

    # Логинимся как организация
    org_login = await client.post("/api/auth/login", json={
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    })
    org_token = org_login.json()["access_token"]
    org_headers = {"Authorization": f"Bearer {org_token}"}

    # Создаем клинику
    clinic_data = {
        "organization_id": org["id"],
        "name": "Test Clinic",
        "location": "Test City",
        "address": "123 Test St"
    }
    clinic_resp = await client.post("/api/clinics/", json=clinic_data, headers=org_headers)
    clinic = clinic_resp.json()

    # Создаем специалиста для создания заказа
    creator_spec_data = generate_specialist_data()
    creator_reg = await client.post("/api/auth/reg", json=creator_spec_data)
    creator = creator_reg.json()

    # Логинимся как специалист для создания заказа
    creator_login = await client.post("/api/auth/login", json={
        "nickname": creator_spec_data["nickname"],
        "password": creator_spec_data["password"]
    })
    creator_token = creator_login.json()["access_token"]
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # Создаем заказ от имени специалиста
    order_data = {
        "service_type": "Consultation",
        "description": "Need help with back pain",
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=creator_headers)
    order = order_resp.json()

    # Обновляем статус заказа на "completed" (от имени специалиста)
    await client.put(
        f"/api/orders/{order['id']}/status",
        json={"status": OrderStatus.COMPLETED.value},
        headers=creator_headers
    )

    review_data = {
        "order_id": order["id"],
        "target_id": clinic["id"],
        "target_type": "clinic",
        "text": "Great service 1!",
        "rate": 8
    }
    await client.post("/api/reviews/", json=review_data, headers=headers)

    # Получаем отзывы для клиники
    response = await client.get(f"/api/reviews/target/clinic/{clinic['id']}", headers=headers)
    print(response.json())
    assert response.status_code == 200

    reviews = response.json()
    assert len(reviews) == 1
    assert all(review["target_type"] == "clinic" for review in reviews)
    assert all(review["target_id"] == clinic["id"] for review in reviews)


@pytest.mark.asyncio
async def test_update_and_delete_review(
        client: AsyncClient,
        patient_data: dict,
        organization_data: dict
):
    # Регистрируем пациента
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    patient = patient_reg.json()

    # Логинимся как пациент
    login = await client.post("/api/auth/login", json={
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Регистрируем организацию
    org_reg = await client.post("/api/auth/reg", json=organization_data)
    org = org_reg.json()

    # Логинимся как организация
    org_login = await client.post("/api/auth/login", json={
        "nickname": organization_data["nickname"],
        "password": organization_data["password"]
    })
    org_token = org_login.json()["access_token"]
    org_headers = {"Authorization": f"Bearer {org_token}"}

    # Создаем клинику
    clinic_data = {
        "organization_id": org["id"],
        "name": "Test Clinic",
        "location": "Test City",
        "address": "123 Test St"
    }
    clinic_resp = await client.post("/api/clinics/", json=clinic_data, headers=org_headers)
    clinic = clinic_resp.json()

    # Создаем специалиста для создания заказа
    creator_spec_data = generate_specialist_data()
    creator_reg = await client.post("/api/auth/reg", json=creator_spec_data)
    creator = creator_reg.json()

    # Логинимся как специалист для создания заказа
    creator_login = await client.post("/api/auth/login", json={
        "nickname": creator_spec_data["nickname"],
        "password": creator_spec_data["password"]
    })
    creator_token = creator_login.json()["access_token"]
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # Создаем заказ от имени специалиста
    order_data = {
        "service_type": "Consultation",
        "description": "Need help with back pain",
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=creator_headers)
    order = order_resp.json()

    # Обновляем статус заказа на "completed" (от имени специалиста)
    await client.put(
        f"/api/orders/{order['id']}/status",
        json={"status": OrderStatus.COMPLETED.value},
        headers=creator_headers
    )

    # Создаем отзыв (от имени пациента)
    review_data = {
        "order_id": order["id"],
        "target_id": clinic["id"],
        "target_type": "clinic",
        "text": "Initial review",
        "rate": 7
    }
    review_resp = await client.post("/api/reviews/", json=review_data, headers=headers)
    review = review_resp.json()

    # Обновляем отзыв (от имени пациента)
    update_data = {
        "text": "Updated review text",
        "rate": 8
    }
    update_resp = await client.put(
        f"/api/reviews/{review['id']}",
        json=update_data,
        headers=headers
    )
    assert update_resp.status_code == 200

    updated_review = update_resp.json()
    assert updated_review["text"] == "Updated review text"
    assert updated_review["rate"] == 8

    # Удаляем отзыв (от имени пациента)
    delete_resp = await client.delete(
        f"/api/reviews/{review['id']}",
        headers=headers
    )
    assert delete_resp.status_code == 204

    # Проверяем, что отзыв удален
    get_resp = await client.get(f"/api/reviews/{review['id']}", headers=headers)
    print(get_resp.json())
    assert get_resp.json()['detail'] == '404: Review not found'