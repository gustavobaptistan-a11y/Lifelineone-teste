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
async def test_ai_orchestrator_reasoning_loop():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Enviar mensagem de agendamento (Simulando entrada via WhatsApp)
        msg_payload_1 = {
            "phone": "5511988887777",
            "message": "Olá, gostaria de agendar uma consulta com especialista em Pneumologia",
            "patient_name": "Gustavo Baptista"
        }
        res_1 = await ac.post("/api/v1/orchestrator/message", json=msg_payload_1)
        assert res_1.status_code == 200, res_1.text
        data_1 = res_1.json()

        assert data_1["detected_intent"] == "agendamento"
        assert "consultar_agenda" in data_1["tools_executed"]
        assert data_1["current_stage"] == "pre_qualificacao"
        assert "Dr. Luiz" in data_1["ai_response"]

        # 2. Enviar mensagem de dúvida sobre convênio
        msg_payload_2 = {
            "phone": "5511988887777",
            "message": "Vocês aceitam o convênio GEAP?"
        }
        res_2 = await ac.post("/api/v1/orchestrator/message", json=msg_payload_2)
        assert res_2.status_code == 200, res_2.text
        data_2 = res_2.json()

        assert data_2["detected_intent"] == "duvida_convenio"
        assert "consultar_convenios" in data_2["tools_executed"]
        assert "GEAP" in data_2["ai_response"]

        # 3. Consultar o Estado do Paciente na plataforma para confirmar que a fonte da verdade foi mantida
        res_state = await ac.get("/api/v1/patients/5511988887777/state")
        assert res_state.status_code == 200
        state = res_state.json()
        assert state["current_intent"] == "duvida_convenio"
        assert state["current_stage"] == "pre_qualificacao"
