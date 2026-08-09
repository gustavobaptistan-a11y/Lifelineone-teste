import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

import app.models.patient
import app.models.journey
import app.models.appointments
import app.models.conversation
import app.models.medical_record
import app.models.ticket

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
async def test_full_patient_journey_e2e_simulation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Executar a simulação de ponta a ponta
        res = await ac.post("/api/v1/simulation/full-journey", json={
            "patient_name": "Gustavo Baptista E2E",
            "phone": "5511988887777"
        })
        assert res.status_code == 200, res.text
        data = res.json()

        assert data["status"] == "success"
        assert len(data["journey_steps_executed"]) == 6

        pep = data["unified_pep_state"]
        assert pep["personal_data"]["name"] == "Gustavo Baptista E2E"
        assert pep["current_stage"] == "alta"
        assert len(pep["exams_data"]) == 1
        assert pep["exams_data"][0]["exam_type"] == "Espirometria"
        assert "VEF1/CVF" in pep["exams_data"][0]["findings"]
