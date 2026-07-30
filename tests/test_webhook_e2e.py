from fastapi.testclient import TestClient

from app.config import settings
from app.services import agendamento_repository
from app.services.evolution_service import evolution_service
from app.services import session_repository
from main import app


def _payload(remote_jid: str, text: str, message_id: str) -> dict:
    return {
        "event": "messages.upsert",
        "instance": "lifeline-test",
        "data": {
            "key": {
                "remoteJid": remote_jid,
                "fromMe": False,
                "id": message_id,
            },
            "pushName": "Paciente Teste",
            "message": {"conversation": text},
            "messageType": "conversation",
        },
    }


def test_webhook_e2e_conversa_com_ids_de_mensagem_diferentes(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "")
    monkeypatch.setattr(settings, "EVOLUTION_SEND_ENABLED", False)
    monkeypatch.setattr(settings, "DATABASE_URL", "")
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_ENABLED", False)
    session_repository._in_memory_sessions.clear()

    client = TestClient(app)
    remote_jid = "5561000000000@s.whatsapp.net"
    mensagens = [
        "Ola, quero agendar uma consulta",
        "Maria Silva",
        "Dor de cabeca ha dois dias",
        "Particular",
        "Sim",
        "manha",
        "1",
    ]
    estados = []

    for index, mensagem in enumerate(mensagens, start=1):
        response = client.post(
            "/webhook",
            json=_payload(remote_jid, mensagem, f"MSG-{index}"),
        )
        assert response.status_code == 200
        body = response.json()
        estados.append(body["estado_final"])
        assert body["envio"]["status"] == "desabilitado"

    assert estados == [
        "aguardando_nome",
        "aguardando_sintoma",
        "aguardando_convenio",
        "aguardando_primeira_consulta",
        "aguardando_preferencia_horario",
        "aguardando_horario",
        "concluido",
    ]
    sessao = session_repository._in_memory_sessions[remote_jid]
    assert sessao["estado"] == "concluido"
    assert sessao["conversation_id"] == "MSG-1"
    assert sessao["last_message_id"] == "MSG-7"


def test_webhook_e2e_envia_respostas_com_evolution_mockada(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "")
    monkeypatch.setattr(settings, "EVOLUTION_SEND_ENABLED", True)
    monkeypatch.setattr(settings, "DATABASE_URL", "")
    monkeypatch.setattr(settings, "GOOGLE_CALENDAR_ENABLED", False)
    session_repository._in_memory_sessions.clear()

    envios = []
    agendamentos = []

    async def fake_send_text_message(remote_jid: str, text: str):
        envios.append({"remote_jid": remote_jid, "text": text})
        return {"status": "enviado", "http_status": 201}

    async def fake_salvar_agendamento_async(remote_jid: str, dados_sessao: dict):
        agendamentos.append({"remote_jid": remote_jid, "dados": dict(dados_sessao)})

    monkeypatch.setattr(
        evolution_service,
        "send_text_message",
        fake_send_text_message,
    )
    monkeypatch.setattr(
        agendamento_repository.agendamento_repository,
        "salvar_agendamento_async",
        fake_salvar_agendamento_async,
    )

    client = TestClient(app)
    remote_jid = "5561000000001@s.whatsapp.net"
    mensagens = [
        "Ola, quero agendar uma consulta",
        "Maria Silva",
        "Dor de cabeca ha dois dias",
        "Particular",
        "Sim",
        "manha",
        "1",
    ]

    for index, mensagem in enumerate(mensagens, start=1):
        response = client.post(
            "/webhook",
            json=_payload(remote_jid, mensagem, f"ENVIO-{index}"),
        )
        assert response.status_code == 200
        assert response.json()["envio"] == {"status": "enviado", "http_status": 201}

    assert len(envios) == len(mensagens)
    assert all(envio["remote_jid"] == remote_jid for envio in envios)
    assert "Agendamento confirmado, Maria Silva" in envios[-1]["text"]
    assert len(agendamentos) == 1
    assert agendamentos[0]["dados"]["estado"] == "concluido"
