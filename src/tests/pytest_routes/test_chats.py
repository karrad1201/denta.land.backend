import pytest
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_chat_flow(client: AsyncClient, patient_data: dict, specialist_data: dict, caplog):
    """
    Тестирует полный цикл работы с чатами: отправку сообщения,
    получение списка чатов и получение сообщений в чате.
    """
    # Установка уровня логирования для теста
    caplog.set_level(logging.DEBUG)
    logger.info("--- Starting test_chat_flow ---")

    # Шаг 1: Регистрация пациента
    logger.info("Step 1: Registering patient...")
    patient_reg = await client.post("/api/auth/reg", json=patient_data)
    logger.info(f"Patient registration response: {patient_reg.status_code}, {patient_reg.text}")
    assert patient_reg.status_code == 201, f"Patient registration failed: {patient_reg.text}"
    patient = patient_reg.json()

    # Шаг 2: Регистрация специалиста
    logger.info("Step 2: Registering specialist...")
    specialist_reg = await client.post("/api/auth/reg", json=specialist_data)
    logger.info(f"Specialist registration response: {specialist_reg.status_code}, {specialist_reg.text}")
    assert specialist_reg.status_code == 201, f"Specialist registration failed: {specialist_reg.text}"
    specialist = specialist_reg.json()

    # Шаг 3: Логин пациента
    logger.info("Step 3: Logging in as patient...")
    login_patient = await client.post("/api/auth/login", json={
        "nickname": patient_data["nickname"],
        "password": patient_data["password"]
    })
    logger.info(f"Patient login response: {login_patient.status_code}, {login_patient.text}")
    assert login_patient.status_code == 200, f"Patient login failed: {login_patient.text}"
    token_patient = login_patient.json()["access_token"]
    headers_patient = {"Authorization": f"Bearer {token_patient}"}

    # Шаг 4: Отправка сообщения пациентом специалисту
    logger.info("Step 4: Patient sends a message to specialist...")
    message_data = {"recipient_id": specialist["id"], "text": "Hello, doctor!"}
    message_resp = await client.post("/api/chat/send-text", json=message_data, headers=headers_patient)

    # Улучшенный вывод логов в случае ошибки
    if message_resp.status_code != 201:
        # Этот блок будет выполнен только при ошибке, и он распечатает
        # все захваченные логи без рекурсии, что предотвратит MemoryError
        print("\n--- CAPTURED LOGS START ---")
        print(caplog.text)
        print("--- CAPTURED LOGS END ---")

    assert message_resp.status_code == 201, f"Send message failed: {message_resp.text}"
    response_data = message_resp.json()
    chat_id = response_data["chat_id"]
    assert isinstance(chat_id, int)

    # Шаг 5: Получение чатов пациента
    logger.info("Step 5: Getting patient's chats...")
    chats_response = await client.get("/api/chat/chats", headers=headers_patient)
    logger.info(f"Get chats response: {chats_response.status_code}, {chats_response.text}")
    assert chats_response.status_code == 200, f"Get chats failed: {chats_response.text}"
    chats = chats_response.json()
    assert len(chats) == 1, "There should be exactly one chat."
    assert chats[0]["id"] == chat_id, "Returned chat ID does not match"

    # Шаг 6: Получение сообщений из чата
    logger.info(f"Step 6: Getting messages for chat ID: {chat_id}...")
    # messages_response = await client.get(f"/api/chat/{chat_id}/messages", headers=headers_patient)
    # Здесь предполагается, что вы уже исправили роутер,
    # и эндпоинт для получения сообщений теперь выглядит так:
    messages_response = await client.get(f"/api/chat/{chat_id}", headers=headers_patient)
    logger.info(f"Get messages response: {messages_response.status_code}, {messages_response.text}")
    assert messages_response.status_code == 200, f"Get messages failed: {messages_response.text}"
    chat_with_messages = messages_response.json()
    messages = chat_with_messages["messages"]
    assert len(messages) == 1, "There should be exactly one message in the chat."
    assert messages[0]["text"] == "Hello, doctor!", "Message text does not match."
    assert messages[0]["sender_id"] == patient["id"], "Sender ID does not match patient ID."

    logger.info("--- Test test_chat_flow finished successfully ---")