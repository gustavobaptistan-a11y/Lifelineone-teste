import asyncio

from app.services import evolution_service as service_module


class FakeResponse:
    status_code = 201
    is_error = False


class FakeClient:
    payload = None

    def __init__(self, **kwargs):
        self.options = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url, json, headers):
        FakeClient.payload = {"url": url, "json": json, "headers": headers}
        return FakeResponse()


def test_send_text_message_is_disabled_by_default():
    service = service_module.EvolutionService()
    result = asyncio.run(
        service.send_text_message("5511999999999@s.whatsapp.net", "Ola")
    )

    assert result == {"status": "desabilitado"}


def test_send_text_message_normalizes_jid_and_sends_payload(monkeypatch):
    monkeypatch.setattr(service_module.httpx, "AsyncClient", FakeClient)
    service = service_module.EvolutionService()
    service.enabled = True
    service.api_key = "test-key"
    service.instance = "test-instance"

    result = asyncio.run(
        service.send_text_message("5511999999999@s.whatsapp.net", "Ola")
    )

    assert result == {"status": "enviado", "http_status": 201}
    assert FakeClient.payload["json"] == {
        "number": "5511999999999",
        "text": "Ola",
    }
