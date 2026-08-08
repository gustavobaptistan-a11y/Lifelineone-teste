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
async def test_patient_state_and_journey_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Criar Lead/Paciente
        payload = {
            "name": "Gustavo Baptista",
            "phone": "5511999998888",
            "email": "gustavo@lifeline.one",
            "insurance_name": "GEAP",
            "attending_doctor": "Dr. Luiz",
            "specialty": "Pneumologia"
        }
        res_create = await ac.post("/api/v1/patients/", json=payload)
        assert res_create.status_code == 201, res_create.text
        data_created = res_create.json()
        
        patient_id = data_created["patient_id"]
        assert data_created["personal_data"]["name"] == "Gustavo Baptista"
        assert data_created["insurance"]["name"] == "GEAP"
        assert data_created["medical_info"]["attending_doctor"] == "Dr. Luiz"
        assert data_created["current_stage"] == "lead_criado"

        # 2. Consultar Estado do Paciente pelo Telefone (simulando a IA no WhatsApp)
        res_state_phone = await ac.get(f"/api/v1/patients/5511999998888/state")
        assert res_state_phone.status_code == 200, res_state_phone.text
        state_data = res_state_phone.json()
        assert state_data["patient_id"] == patient_id
        assert state_data["current_stage"] == "lead_criado"

        # 3. Atualizar Tratamento, Diagnóstico, Retorno e Intenção Atual (exemplo da página 3/4 do PDF)
        update_payload = {
            "active_treatment": "Tratamento ativo para Rinite",
            "current_intent": "duvida_retorno",
            "pending_tasks": [{"id": 1, "task": "Enviar recibo para reembolso"}],
            "exams_data": [{"exam": "Espirometria", "status": "agendado"}]
        }
        res_update = await ac.patch(f"/api/v1/patients/{patient_id}", json=update_payload)
        assert res_update.status_code == 200, res_update.text
        updated_state = res_update.json()
        assert updated_state["active_treatment"] == "Tratamento ativo para Rinite"
        assert updated_state["current_intent"] == "duvida_retorno"
        assert len(updated_state["pending_tasks"]) == 1
        assert len(updated_state["exams_data"]) == 1

        # 4. Transicionar Etapa da Jornada: lead_criado -> agendamento
        trans_payload_1 = {
            "to_stage": "agendamento",
            "trigger_event": "appointment_scheduled",
            "notes": "Consulta agendada para 10/08 com Dr. Luiz"
        }
        res_trans1 = await ac.post(f"/api/v1/journey/{patient_id}/transition", json=trans_payload_1)
        assert res_trans1.status_code == 200, res_trans1.text
        assert res_trans1.json()["current_stage"] == "agendamento"

        # 5. Transicionar Etapa da Jornada: agendamento -> consulta_realizada
        trans_payload_2 = {
            "to_stage": "consulta_realizada",
            "trigger_event": "appointment_completed",
            "notes": "Consulta realizada em 10/08. Diagnóstico: Rinite"
        }
        res_trans2 = await ac.post(f"/api/v1/journey/{patient_id}/transition", json=trans_payload_2)
        assert res_trans2.status_code == 200, res_trans2.text
        assert res_trans2.json()["current_stage"] == "consulta_realizada"

        # 6. Consultar Histórico de Jornada
        res_history = await ac.get(f"/api/v1/journey/{patient_id}/history")
        assert res_history.status_code == 200, res_history.text
        history = res_history.json()
        assert len(history) == 3 # lead_created, agendamento, consulta_realizada
        assert history[0]["to_stage"] == "consulta_realizada"
        assert history[1]["to_stage"] == "agendamento"
        assert history[2]["to_stage"] == "lead_criado"
