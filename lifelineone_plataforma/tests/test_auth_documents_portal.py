import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

import app.models.patient
import app.models.journey
import app.models.appointments
import app.models.conversation
import app.models.medical_record
import app.models.ticket
import app.models.audit
import app.models.lab_order
import app.models.user

from app.main import app
from app.core.database import engine, Base
from app.services.event_handlers import setup_event_handlers

@pytest_asyncio.fixture(autouse=True)
async def init_db():
    setup_event_handlers()
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_auth_rbac_documents_and_patient_portal():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Seed Usuários Padrão (RBAC)
        res_seed = await ac.post("/api/v1/auth/seed-users")
        assert res_seed.status_code == 200
        assert len(res_seed.json()["created_emails"]) >= 4

        # 2. Testar Login Médico e Obtenção de Token JWT
        res_login = await ac.post("/api/v1/auth/login", json={
            "email": "medico@lifeline.com",
            "password": "123"
        })
        assert res_login.status_code == 200
        auth_data = res_login.json()
        assert "access_token" in auth_data
        assert auth_data["role"] == "medico"
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Criar Paciente para Testes
        res_p = await ac.post("/api/v1/patients/", json={
            "name": "Paciente Teste PDF Portal",
            "phone": "5511988887777"
        }, headers=headers)
        assert res_p.status_code == 201
        patient_id = res_p.json()["patient_id"]

        # 4. Baixar PDF Oficial do Prontuário Unificado
        res_pdf = await ac.get(f"/api/v1/documents/pep-pdf/{patient_id}", headers=headers)
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"
        assert len(res_pdf.content) > 500 # Arquivo PDF válido gerado pelo ReportLab

        # 5. Testar Portal do Paciente
        res_portal = await ac.get("/api/v1/patient-portal/my-dashboard", headers=headers)
        assert res_portal.status_code == 200
        portal_data = res_portal.json()
        assert "patient" in portal_data
        assert "released_exams" in portal_data
