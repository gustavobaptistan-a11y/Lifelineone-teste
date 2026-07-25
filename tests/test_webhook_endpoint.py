from fastapi.testclient import TestClient
from app.config import settings
from main import app


def make_evolution_payload(remote_jid: str):
    return {
        "event": "messages.upsert",
        "instance": "lifeline",
        "data": {
            "key": {
                "remoteJid": remote_jid,
                "fromMe": False,
                "id": "TEST_MSG_ID_1"
            },
            "pushName": "Carlos Eduardo",
            "message": {
                "conversation": "Olá, eu quero agendar uma consulta"
            },
            "messageType": "conversation"
        }
    }


class FakeEvolutionResponse:
    status_code = 201
    is_error = False


class FakeAsyncClient:
    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url, json, headers):
        return FakeEvolutionResponse()


async def fake_obter_sessao_async(remote_jid: str):
    return {"estado": "inicio"}


async def fake_salvar_sessao_async(remote_jid: str, dados_sessao: dict):
    return None


async def fake_salvar_agendamento_async(remote_jid: str, dados_sessao: dict):
    return None


def test_webhook_endpoint_accepts_valid_webhook_secret(monkeypatch):
    client = TestClient(app)
    payload = make_evolution_payload("5561999990001@s.whatsapp.net")

    monkeypatch.setattr("app.services.evolution_service.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("app.services.session_repository.obter_sessao_async", fake_obter_sessao_async)
    monkeypatch.setattr("app.services.session_repository.salvar_sessao_async", fake_salvar_sessao_async)
    import app.services.agendamento_repository as agendamento_module
    monkeypatch.setattr(agendamento_module.agendamento_repository, "salvar_agendamento_async", fake_salvar_agendamento_async)
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "test-secret")

    response = client.post(
        "/webhook",
        json=payload,
        headers={"X-Webhook-Secret": "test-secret"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"sucesso", "ignorado"}
    assert data["envio"]["status"] in {"desabilitado", "enviado"}


def test_webhook_endpoint_rejects_missing_webhook_secret(monkeypatch):
    client = TestClient(app)
    payload = make_evolution_payload("5561999990002@s.whatsapp.net")

    monkeypatch.setattr("app.services.session_repository.obter_sessao_async", fake_obter_sessao_async)
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "test-secret")

    response = client.post("/webhook", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Webhook nao autorizado"
