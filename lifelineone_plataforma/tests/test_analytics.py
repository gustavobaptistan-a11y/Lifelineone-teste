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
async def test_analytics_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Criar 2 pacientes
        await ac.post("/api/v1/patients/", json={"name": "Paciente A", "phone": "5511910001000"})
        p2 = await ac.post("/api/v1/patients/", json={"name": "Paciente B", "phone": "5511920002000"})
        p2_id = p2.json()["patient_id"]

        # Transicionar Paciente B para agendamento
        await ac.post(f"/api/v1/journey/{p2_id}/transition", json={"to_stage": "agendamento"})

        # 2. Consultar Analytics do Funil
        res_funnel = await ac.get("/api/v1/analytics/funnel")
        assert res_funnel.status_code == 200, res_funnel.text
        funnel_data = res_funnel.json()

        assert funnel_data["total_patients"] == 2
        assert len(funnel_data["stages_breakdown"]) == 10

        # Find lead_criado and agendamento breakdown
        lead_stage = next(s for s in funnel_data["stages_breakdown"] if s["stage"] == "lead_criado")
        agendamento_stage = next(s for s in funnel_data["stages_breakdown"] if s["stage"] == "agendamento")

        assert lead_stage["count"] == 1
        assert lead_stage["conversion_rate_percentage"] == 50.0
        assert agendamento_stage["count"] == 1
        assert agendamento_stage["conversion_rate_percentage"] == 50.0

        # 3. Consultar Analytics de Performance da IA
        res_ai = await ac.get("/api/v1/analytics/ai-performance")
        assert res_ai.status_code == 200, res_ai.text
        ai_data = res_ai.json()
        assert "total_messages_processed" in ai_data
        assert "tools_execution_count" in ai_data
