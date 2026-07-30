from fastapi.testclient import TestClient

from app.config import settings
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