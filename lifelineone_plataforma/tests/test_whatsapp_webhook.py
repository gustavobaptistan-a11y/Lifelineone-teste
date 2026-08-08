import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base

@pytest_asyncio.fixture(autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_whatsapp_webhook_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Simular recebimento de mensagem via Webhook da Evolution API
        evolution_payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511955554444@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG_001"
                },
                "pushName": "Paciente WhatsApp Teste",
                "message": {
                    "conversation": "Olá, aceita o convênio GEAP?"
                }
            }
        }

        res_wh = await ac.post("/api/v1/webhooks/whatsapp", json=evolution_payload)
        assert res_wh.status_code == 200, res_wh.text
        data_wh = res_wh.json()

        assert data_wh["status"] == "processed"
        assert data_wh["phone"] == "5511955554444"
        assert data_wh["detected_intent"] == "duvida_convenio"
        assert "GEAP" in data_wh["ai_response"]
        assert data_wh["dispatch_status"]["status"] == "sent"

        # 2. Verificar se o paciente foi registrado na plataforma com estado correto
        res_state = await ac.get("/api/v1/patients/5511955554444/state")
        assert res_state.status_code == 200
        state = res_state.json()
        assert state["personal_data"]["name"] == "Paciente WhatsApp Teste"
        assert state["personal_data"]["phone"] == "5511955554444"
