import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
import logging
import uuid
from src.domain.entity.orders.order import OrderStatus
from src.domain.entity.orders.response import ResponseStatus

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
async def test_create_response(client: AsyncClient, patient_data: dict, specialist_data: dict):
    # Регистрируем пациента
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    logger.info(f"Patient registration response: {patient_reg.status_code}, {patient_reg.text}")
    assert patient_reg.status_code == 201, f"Patient registration failed: {patient_reg.text}"
    patient = patient_reg.json()

    # Регистрируем специалиста (создатель заказа)
    creator_spec_data = generate_specialist_data()
    creator_reg = await client.post("/api/auth/reg", json=creator_spec_data)
    logger.info(f"Order creator registration response: {creator_reg.status_code}, {creator_reg.text}")
    assert creator_reg.status_code == 201, f"Order creator registration failed: {creator_reg.text}"
    order_creator = creator_reg.json()

    # Логинимся как создатель заказа
    login_creator = await client.post("/api/auth/login", json={
        "nickname": creator_spec_data["nickname"],
        "password": creator_spec_data["password"]
    })
    logger.info(f"Order creator login response: {login_creator.status_code}, {login_creator.text}")
    token_creator = login_creator.json()["access_token"]
    headers_creator = {"Authorization": f"Bearer {token_creator}"}

    # Создаем заказ как специалист
    order_data = {
        "service_type": "Consultation",
        "description": "Need help with medical issue",
        "specifications": ["urgent", "online"],
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=headers_creator)
    logger.info(f"Create order response: {order_resp.status_code}, {order_resp.text}")
    assert order_resp.status_code == 201, f"Create order failed: {order_resp.text}"
    order = order_resp.json()

    # Регистрируем специалиста для отклика
    responder_spec_data = generate_specialist_data()
    responder_reg = await client.post("/api/auth/reg", json=responder_spec_data)
    logger.info(f"Responder registration response: {responder_reg.status_code}, {responder_reg.text}")
    assert responder_reg.status_code == 201, f"Responder registration failed: {responder_reg.text}"

    # Логинимся как специалист для создания отклика
    login_responder = await client.post("/api/auth/login", json={
        "nickname": responder_spec_data["nickname"],
        "password": responder_spec_data["password"]
    })
    logger.info(f"Responder login response: {login_responder.status_code}, {login_responder.text}")
    token_responder = login_responder.json()["access_token"]
    headers_responder = {"Authorization": f"Bearer {token_responder}"}

    # Создаем отклик
    response_data = {
        "order_id": order["id"],
        "text": "I can help with your issue"
    }
    response = await client.post("/api/responses/", json=response_data, headers=headers_responder)
    logger.info(f"Create response response: {response.status_code}, {response.text}")
    assert response.status_code == 201, f"Create response failed: {response.text}"

    response_obj = response.json()
    assert response_obj["responser_id"] == responder_reg.json()["id"]
    assert response_obj["role"] == "specialist"
    assert response_obj["status"] == ResponseStatus.PROPOSED.value
    assert response_obj["order_id"] == order["id"]
    assert response_obj["text"] == "I can help with your issue"

    # Проверяем что счетчик откликов увеличился (от лица пациента)
    login_patient = await client.post("/api/auth/login", json={
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    })
    token_patient = login_patient.json()["access_token"]
    headers_patient = {"Authorization": f"Bearer {token_patient}"}

    order_after = await client.get(f"/api/orders/{order['id']}", headers=headers_patient)
    assert order_after.status_code == 200
    assert order_after.json()["responses_count"] == 1

    # Пытаемся создать дубликат отклика - должно быть ошибка
    duplicate_response = await client.post("/api/responses/", json=response_data, headers=headers_responder)
    assert duplicate_response.status_code == 400
    assert "already exists" in duplicate_response.text.lower()


@pytest.mark.asyncio
async def test_accept_response(client: AsyncClient, patient_data: dict, specialist_data: dict):
    # Регистрируем пациента
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    logger.info(f"Patient registration response: {patient_reg.status_code}, {patient_reg.text}")
    assert patient_reg.status_code == 201, f"Patient registration failed: {patient_reg.text}"
    patient = patient_reg.json()

    # Регистрируем специалиста (создатель заказа)
    creator_spec_data = generate_specialist_data()
    creator_reg = await client.post("/api/auth/reg", json=creator_spec_data)
    logger.info(f"Order creator registration response: {creator_reg.status_code}, {creator_reg.text}")
    assert creator_reg.status_code == 201, f"Order creator registration failed: {creator_reg.text}"

    # Логинимся как создатель заказа
    login_creator = await client.post("/api/auth/login", json={
        "nickname": creator_spec_data["nickname"],
        "password": creator_spec_data["password"]
    })
    token_creator = login_creator.json()["access_token"]
    headers_creator = {"Authorization": f"Bearer {token_creator}"}

    # Создаем заказ как специалист
    order_data = {
        "service_type": "Consultation",
        "description": "Need help with medical issue",
        "specifications": ["urgent", "online"],
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=headers_creator)
    logger.info(f"Create order response: {order_resp.status_code}, {order_resp.text}")
    assert order_resp.status_code == 201, f"Create order failed: {order_resp.text}"
    order = order_resp.json()

    # Регистрируем специалиста для отклика
    responder_spec_data = generate_specialist_data()
    responder_reg = await client.post("/api/auth/reg", json=responder_spec_data)
    logger.info(f"Responder registration response: {responder_reg.status_code}, {responder_reg.text}")
    assert responder_reg.status_code == 201, f"Responder registration failed: {responder_reg.text}"
    responder = responder_reg.json()

    # Логинимся как специалист для создания отклика
    login_responder = await client.post("/api/auth/login", json={
        "nickname": responder_spec_data["nickname"],
        "password": responder_spec_data["password"]
    })
    logger.info(f"Responder login response: {login_responder.status_code}, {login_responder.text}")
    token_responder = login_responder.json()["access_token"]
    headers_responder = {"Authorization": f"Bearer {token_responder}"}

    # Создаем отклик
    response_data = {
        "order_id": order["id"],
        "text": "I can help with your issue"
    }
    response_resp = await client.post("/api/responses/", json=response_data, headers=headers_responder)
    logger.info(f"Create response response: {response_resp.status_code}, {response_resp.text}")
    assert response_resp.status_code == 201, f"Create response failed: {response_resp.text}"
    response_obj = response_resp.json()
    response_id = response_obj["response_id"]

    # Пытаемся принять отклик как не создатель - должно быть ошибка
    wrong_accept = await client.put(
        f"/api/responses/{response_id}/accept",
        headers=headers_responder  # Пытается принять откликатель
    )
    assert wrong_accept.status_code == 400, "Only order creator should be able to accept responses"

    # Принимаем отклик как создатель заказа
    accept_resp = await client.put(
        f"/api/responses/{response_id}/accept",
        headers=headers_creator  # Принимает создатель заказа
    )
    logger.info(f"Accept response response: {accept_resp.status_code}, {accept_resp.text}")
    assert accept_resp.status_code == 200, f"Accept response failed: {accept_resp.text}"

    accepted_response = accept_resp.json()
    assert accepted_response["status"] == ResponseStatus.TAKEN.value

    # Проверяем что заказ завершен
    order_after = await client.get(f"/api/orders/{order['id']}", headers=headers_creator)
    assert order_after.status_code == 200
    assert order_after.json()["status"] == OrderStatus.COMPLETED.value

    # Проверяем что остальные отклики отклонены
    responses = await client.get(f"/api/responses/order/{order['id']}", headers=headers_creator)
    assert responses.status_code == 200
    for resp in responses.json():
        if resp["response_id"] == response_id:
            assert resp["status"] == ResponseStatus.TAKEN.value
        else:
            assert resp["status"] == ResponseStatus.DENIED.value


@pytest.mark.asyncio
async def test_deny_and_delete_response(client: AsyncClient, patient_data: dict, specialist_data: dict):
    # Регистрируем пациента
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    assert patient_reg.status_code == 201
    patient = patient_reg.json()

    # Регистрируем специалиста (создатель заказа)
    creator_spec_data = generate_specialist_data()
    creator_reg = await client.post("/api/auth/reg", json=creator_spec_data)
    assert creator_reg.status_code == 201
    order_creator = creator_reg.json()

    # Логинимся как создатель заказа
    login_creator = await client.post("/api/auth/login", json={
        "nickname": creator_spec_data["nickname"],
        "password": creator_spec_data["password"]
    })
    token_creator = login_creator.json()["access_token"]
    headers_creator = {"Authorization": f"Bearer {token_creator}"}

    # Создаем заказ как специалист
    order_data = {
        "service_type": "Consultation",
        "description": "Need help with medical issue",
        "specifications": ["urgent", "online"],
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=headers_creator)
    assert order_resp.status_code == 201
    order = order_resp.json()

    # Регистрируем первого специалиста для отклика
    responder1_data = generate_specialist_data()
    responder1_reg = await client.post("/api/auth/reg", json=responder1_data)
    assert responder1_reg.status_code == 201
    responder1 = responder1_reg.json()

    # Логинимся как первый специалист
    login_responder1 = await client.post("/api/auth/login", json={
        "nickname": responder1_data["nickname"],
        "password": responder1_data["password"]
    })
    token_responder1 = login_responder1.json()["access_token"]
    headers_responder1 = {"Authorization": f"Bearer {token_responder1}"}

    # Создаем отклик от первого специалиста
    response_data = {
        "order_id": order["id"],
        "text": "I can help with your issue"
    }
    response_resp1 = await client.post("/api/responses/", json=response_data, headers=headers_responder1)
    assert response_resp1.status_code == 201
    response_obj1 = response_resp1.json()
    response_id1 = response_obj1["response_id"]

    # Регистрируем второго специалиста для отклика
    responder2_data = generate_specialist_data()
    responder2_reg = await client.post("/api/auth/reg", json=responder2_data)
    assert responder2_reg.status_code == 201
    responder2 = responder2_reg.json()

    # Логинимся как второй специалист
    login_responder2 = await client.post("/api/auth/login", json={
        "nickname": responder2_data["nickname"],
        "password": responder2_data["password"]
    })
    token_responder2 = login_responder2.json()["access_token"]
    headers_responder2 = {"Authorization": f"Bearer {token_responder2}"}

    # Создаем отклик от второго специалиста
    response_resp2 = await client.post("/api/responses/", json=response_data, headers=headers_responder2)
    assert response_resp2.status_code == 201
    response_obj2 = response_resp2.json()
    response_id2 = response_obj2["response_id"]

    # Отклоняем первый отклик (от первого специалиста)
    deny_resp = await client.put(
        f"/api/responses/{response_id1}/deny",
        headers=headers_responder1
    )
    assert deny_resp.status_code == 200
    denied_response = deny_resp.json()
    assert denied_response["status"] == ResponseStatus.DENIED.value

    # Удаляем второй отклик (от второго специалиста)
    delete_resp = await client.delete(
        f"/api/responses/{response_id2}",
        headers=headers_responder2
    )
    assert delete_resp.status_code == 204

    # Проверяем что второй отклик удален
    get_resp = await client.get(f"/api/responses/{response_id2}", headers=headers_responder2)
    assert get_resp.status_code == 404

    # Проверяем счетчик откликов (от лица пациента)
    login_patient = await client.post("/api/auth/login", json={
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    })
    token_patient = login_patient.json()["access_token"]
    headers_patient = {"Authorization": f"Bearer {token_patient}"}

    # Убедимся, что пациент имеет доступ к заказу
    order_after = await client.get(f"/api/orders/{order['id']}", headers=headers_patient)
    assert order_after.status_code == 200
    assert order_after.json()["responses_count"] == 1  # Остался только отклоненный отклик первого специалиста


@pytest.mark.asyncio
async def test_invalid_response_actions(client: AsyncClient, patient_data: dict, specialist_data: dict):
    # Регистрируем пациента
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    assert patient_reg.status_code == 201
    patient = patient_reg.json()

    # Регистрируем специалиста (создатель заказа)
    creator_spec_data = generate_specialist_data()
    creator_reg = await client.post("/api/auth/reg", json=creator_spec_data)
    assert creator_reg.status_code == 201
    order_creator = creator_reg.json()

    # Логинимся как создатель заказа
    login_creator = await client.post("/api/auth/login", json={
        "nickname": creator_spec_data["nickname"],
        "password": creator_spec_data["password"]
    })
    token_creator = login_creator.json()["access_token"]
    headers_creator = {"Authorization": f"Bearer {token_creator}"}

    # Создаем заказ как специалист
    order_data = {
        "service_type": "Consultation",
        "description": "Need help with medical issue",
        "specifications": ["urgent", "online"],
        "preferred_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "patient_id": patient["id"]  # Указываем пациента
    }
    order_resp = await client.post("/api/orders/", json=order_data, headers=headers_creator)
    assert order_resp.status_code == 201
    order = order_resp.json()

    # Логинимся как пациент
    login_patient = await client.post("/api/auth/login", json={
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    })
    token_patient = login_patient.json()["access_token"]
    headers_patient = {"Authorization": f"Bearer {token_patient}"}

    response_data = {
        "order_id": order["id"],
        "text": "I can help"
    }

    # Регистрируем специалиста для отклика
    responder_spec_data = generate_specialist_data()
    responder_reg = await client.post("/api/auth/reg", json=responder_spec_data)
    assert responder_reg.status_code == 201
    responder = responder_reg.json()

    # Логинимся как специалист
    login_responder = await client.post("/api/auth/login", json={
        "nickname": responder_spec_data["nickname"],
        "password": responder_spec_data["password"]
    })
    token_responder = login_responder.json()["access_token"]
    headers_responder = {"Authorization": f"Bearer {token_responder}"}

    # Создаем отклик
    response_resp = await client.post("/api/responses/", json=response_data, headers=headers_responder)
    assert response_resp.status_code == 201
    response_obj = response_resp.json()
    response_id = response_obj["response_id"]

    # Пытаемся удалить отклик как пациент (не владелец) - должно быть запрещено
    invalid_delete = await client.delete(
        f"/api/responses/{response_id}",
        headers=headers_patient
    )
    assert invalid_delete.status_code == 400

    # Принимаем отклик как создатель
    accept_resp = await client.put(
        f"/api/responses/{response_id}/accept",
        headers=headers_creator
    )
    assert accept_resp.status_code == 200

    # Пытаемся удалить принятый отклик - должно быть запрещено
    delete_accepted = await client.delete(
        f"/api/responses/{response_id}",
        headers=headers_responder
    )
    assert delete_accepted.status_code == 400