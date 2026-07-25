from app.models.schemas import WebhookPayload
from pydantic import ValidationError


def test_webhook_payload_accepts_evolution_message():
    payload = {
        "event": "messages.upsert",
        "instance": "lifeline",
        "data": {
            "key": {
                "remoteJid": "5561988887777@s.whatsapp.net",
                "fromMe": False,
                "id": "ABC123"
            },
            "pushName": "Carlos Eduardo",
            "message": {
                "conversation": "Olá, qual é o horário disponível?"
            },
            "messageType": "conversation"
        }
    }

    webhook = WebhookPayload(**payload)

    assert webhook.event == "messages.upsert"
    assert webhook.instance == "lifeline"
    assert webhook.data.key.remote_jid == "5561988887777@s.whatsapp.net"
    assert webhook.data.push_name == "Carlos Eduardo"
    assert webhook.data.message.conversation == "Olá, qual é o horário disponível?"


def test_webhook_payload_rejects_invalid_remote_jid():
    payload = {
        "data": {
            "key": {
                "remoteJid": "",
                "fromMe": False
            },
            "message": {
                "conversation": "Olá"
            }
        }
    }

    try:
        WebhookPayload(**payload)
        assert False, "Deveria falhar em remoteJid vazio"
    except ValidationError as exc:
        assert "remoteJid" in str(exc)
