import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base
from app.services.event_handlers import setup_event_handlers

@pytest_asyncio.fixture(autouse=True)
async def init_db():
    setup_event_handlers()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_hybrid_handover_ticket_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Criar paciente
        res_p = await ac.post("/api/v1/patients/", json={
            "name": "Paciente Hibrido",
            "phone": "5511977776666"
        })
        assert res_p.status_code == 201
        patient_id = res_p.json()["patient_id"]

        # 2. Criar Ticket de Atendimento Humano
        res_tk = await ac.post("/api/v1/tickets/create", json={
            "patient_id": patient_id,
            "reason": "Dúvida sobre valor de cirurgia"
        })
        assert res_tk.status_code == 200
        ticket_id = res_tk.json()["id"]

        # 3. Atendente Humano assume o ticket
        res_takeover = await ac.post(f"/api/v1/tickets/{ticket_id}/takeover", json={
            "agent_name": "Dra. Renata"
        })
        assert res_takeover.status_code == 200
        assert res_takeover.json()["status"] == "assumido_humano"

        # 4. Enviar mensagem para o Orquestrador -> IA deve pausar e indicar transbordo humano!
        res_msg1 = await ac.post("/api/v1/orchestrator/message", json={
            "phone": "5511977776666",
            "message": "Olá, Dra. Renata, quanto custa a consulta?"
        })
        assert res_msg1.status_code == 200
        data1 = res_msg1.json()
        assert data1["detected_intent"] == "transbordo_humano"
        assert "Dra. Renata" in data1["ai_response"]

        # 5. Atendente Humano devolve o controle para a IA
        res_release = await ac.post(f"/api/v1/tickets/{ticket_id}/release")
        assert res_release.status_code == 200
        assert res_release.json()["status"] == "encerrado"

        # 6. Enviar nova mensagem -> IA reassume automaticamente!
        res_msg2 = await ac.post("/api/v1/orchestrator/message", json={
            "phone": "5511977776666",
            "message": "Gostaria de agendar um horário"
        })
        assert res_msg2.status_code == 200
        data2 = res_msg2.json()
        assert data2["detected_intent"] == "agendamento"
        assert "consultar_agenda" in data2["tools_executed"]
