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
async def test_event_driven_architecture():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Criar um paciente para os eventos
        res_p = await ac.post("/api/v1/patients/", json={
            "name": "Paciente Evento",
            "phone": "5511977776666"
        })
        assert res_p.status_code == 201
        patient_id = res_p.json()["patient_id"]

        # 2. Disparar Evento: consulta_realizada
        res_ev1 = await ac.post("/api/v1/events/publish", json={
            "event_type": "consulta_realizada",
            "patient_id": patient_id,
            "data": {"doctor": "Dr. Luiz", "notes": "Rinite alérgica", "return_date": "2026-09-10"}
        })
        assert res_ev1.status_code == 200, res_ev1.text
        data_ev1 = res_ev1.json()
        assert data_ev1["new_stage"] == "consulta_realizada"
        assert "jornada_atualizada_e_followup_criado" in data_ev1["actions_triggered"]

        # 3. Disparar Evento: exame_disponivel
        res_ev2 = await ac.post("/api/v1/events/publish", json={
            "event_type": "exame_disponivel",
            "patient_id": patient_id,
            "data": {"exam_name": "Espirometria"}
        })
        assert res_ev2.status_code == 200, res_ev2.text
        data_ev2 = res_ev2.json()
        assert data_ev2["new_stage"] == "exames"
        assert "notificacao_exame_enviada" in data_ev2["actions_triggered"]

        # 4. Disparar Evento: pagamento_confirmado
        res_ev3 = await ac.post("/api/v1/events/publish", json={
            "event_type": "pagamento_confirmado",
            "patient_id": patient_id,
            "data": {"amount": "R$ 350,00"}
        })
        assert res_ev3.status_code == 200, res_ev3.text
        data_ev3 = res_ev3.json()
        assert data_ev3["new_stage"] == "tratamento"

        # 5. Disparar Evento: paciente_inativo_180_dias
        res_ev4 = await ac.post("/api/v1/events/publish", json={
            "event_type": "paciente_inativo_180_dias",
            "patient_id": patient_id,
            "data": {}
        })
        assert res_ev4.status_code == 200, res_ev4.text
        data_ev4 = res_ev4.json()
        assert data_ev4["new_stage"] == "reativacao"

        # 6. Consultar Estado do Paciente e Histórico de Jornada para validar integridade
        res_state = await ac.get(f"/api/v1/patients/{patient_id}/state")
        assert res_state.status_code == 200
        state = res_state.json()
        assert state["current_stage"] == "reativacao"
        assert len(state["pending_tasks"]) >= 2
