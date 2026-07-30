import json

import pytest
import httpx
import respx
from app.services.evolution_service import EvolutionService
from app.config import settings

@pytest.fixture
def evolution_service():
    return EvolutionService()

@pytest.mark.asyncio
@respx.mock
async def test_create_instance_success(evolution_service: EvolutionService):
    instance_name = "test_instance"
    mock_response = {"instance": {"instanceName": instance_name}}
    respx.post(f"{settings.EVOLUTION_API_URL}/instance/create").mock(return_value=httpx.Response(200, json=mock_response))

    result = await evolution_service.create_instance(instance_name)
    assert result == mock_response

@pytest.mark.asyncio
@respx.mock
async def test_create_instance_error(evolution_service: EvolutionService):
    instance_name = "test_instance"
    respx.post(f"{settings.EVOLUTION_API_URL}/instance/create").mock(return_value=httpx.Response(500))

    result = await evolution_service.create_instance(instance_name)
    assert result is None

@pytest.mark.asyncio
@respx.mock
async def test_get_qrcode_success(evolution_service: EvolutionService):
    instance_name = "test_instance"
    mock_qr_code = b"qr_code_image_data"
    respx.get(f"{settings.EVOLUTION_API_URL}/instance/{instance_name}/qrcode").mock(return_value=httpx.Response(200, content=mock_qr_code))

    result = await evolution_service.get_qrcode(instance_name)
    assert result == mock_qr_code

@pytest.mark.asyncio
@respx.mock
async def test_get_qrcode_error(evolution_service: EvolutionService):
    instance_name = "test_instance"
    respx.get(f"{settings.EVOLUTION_API_URL}/instance/{instance_name}/qrcode").mock(return_value=httpx.Response(500))

    result = await evolution_service.get_qrcode(instance_name)
    assert result is None

@pytest.mark.asyncio
@respx.mock
async def test_send_message_success(evolution_service: EvolutionService):
    instance_name = "test_instance"
    phone_number = "123456789"
    message = "Hello, world!"
    settings.EVOLUTION_SEND_ENABLED = True
    mock_response = {"status": "success"}
    route = respx.post(
        f"{settings.EVOLUTION_API_URL}/message/sendText/{instance_name}"
    ).mock(return_value=httpx.Response(200, json=mock_response))

    result = await evolution_service.send_message(instance_name, phone_number, message)

    assert result == mock_response
    assert route.calls.last.request.headers["apikey"] == settings.EVOLUTION_API_KEY
    assert json.loads(route.calls.last.request.read()) == {
        "number": "123456789",
        "text": "Hello, world!",
    }

@pytest.mark.asyncio
async def test_send_message_disabled(evolution_service: EvolutionService):
    instance_name = "test_instance"
    phone_number = "123456789"
    message = "Hello, world!"
    settings.EVOLUTION_SEND_ENABLED = False

    result = await evolution_service.send_message(instance_name, phone_number, message)
    assert result == {"status": "disabled"}

@pytest.mark.asyncio
@respx.mock
async def test_send_message_error(evolution_service: EvolutionService):
    instance_name = "test_instance"
    phone_number = "123456789"
    message = "Hello, world!"
    settings.EVOLUTION_SEND_ENABLED = True
    respx.post(f"{settings.EVOLUTION_API_URL}/message/sendText/{instance_name}").mock(return_value=httpx.Response(500))

    result = await evolution_service.send_message(instance_name, phone_number, message)
    assert result is None
