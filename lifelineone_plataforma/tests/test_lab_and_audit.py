import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

import app.models.patient
import app.models.journey
import app.models.appointments
import app.models.conversation
import app.models.medical_record
import app.models.ticket
import app.models.audit
import app.models.lab_order

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
async def test_lab_workflow_auditing_and_guard_ai():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Criar paciente
        res_p = await ac.post("/api/v1/patients/", json={
            "name": "Paciente Laboratorio Master",
            "phone": "5511911112222"
        })
        assert res_p.status_code == 201
        patient_id = res_p.json()["patient_id"]

        # 2. Criar pedido de exame laboratorial pelo médico
        res_order = await ac.post("/api/v1/lab-audit/orders", json={
            "patient_id": patient_id,
            "exam_name": "Espirometria Completa",
            "requesting_doctor": "Dr. Carlos Pneumologia",
            "unit_location": "Unidade Jardins - SP"
        })
        assert res_order.status_code == 200, res_order.text
        order_data = res_order.json()
        order_id = order_data["lab_order_id"]
        assert order_data["current_stage"] == "contato_whatsapp"

        # 3. Avançar status do laboratório até liberação no Cofre de Segurança (Vault)
        res_step1 = await ac.post(f"/api/v1/lab-audit/orders/{order_id}/status", json={
            "next_status": "coleta_agendada",
            "scheduled_date": "18/08 às 08:30 (Unidade Jardins)",
            "actor_name": "Recepção Jardins"
        })
        assert res_step1.status_code == 200
        assert res_step1.json()["new_status"] == "coleta_agendada"

        res_vault = await ac.post(f"/api/v1/lab-audit/orders/{order_id}/status", json={
            "next_status": "liberado_cofre_segura",
            "findings_summary": "Espirometria sem broncodistúrbio. Laudo assinado digitalmente.",
            "actor_name": "Bioquímico Dr. Silva"
        })
        assert res_vault.status_code == 200
        vault_data = res_vault.json()
        assert vault_data["new_status"] == "liberado_cofre_segura"
        assert "AES256:" in vault_data["vault_file_hash"]

        # 4. Verificar Auditoria de Acesso e Guardião de IA
        res_audit = await ac.get(f"/api/v1/lab-audit/audit/integrity/{patient_id}")
        assert res_audit.status_code == 200
        audit_data = res_audit.json()
        assert audit_data["total_access_logs"] >= 3
        assert audit_data["anomalies_detected"] == 0
        assert audit_data["integrity_score"] == "100%"

        # 5. Registrar Decisão Médica Pós-Consulta
        res_decision = await ac.post("/api/v1/lab-audit/clinical-decision/post-consultation", json={
            "patient_id": patient_id,
            "decision": "alta",
            "doctor_notes": "Paciente totalmente assintomático. Laudo perfeitamente limpo."
        })
        assert res_decision.status_code == 200
        assert res_decision.json()["decision"] == "alta"
