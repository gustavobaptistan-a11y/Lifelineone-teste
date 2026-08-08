import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base, AsyncSessionLocal
from app.models.patient import Patient
from app.services.scheduler_service import scheduler_service
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
async def test_scheduler_inactive_patients_180d():
    async with AsyncSessionLocal() as db:
        # 1. Criar um paciente inativo há mais de 180 dias
        old_date = datetime.now(timezone.utc) - timedelta(days=190)
        patient_inactive = Patient(
            name="Paciente Antigo Inativo",
            phone="5511911112222",
            last_interaction=old_date
        )
        db.add(patient_inactive)
        await db.commit()
        await db.refresh(patient_inactive)

        # 2. Executar a verificação de inatividade de 180 dias do Scheduler
        events_dispatched = await scheduler_service.check_inactive_patients(db)
        assert len(events_dispatched) == 1
        assert events_dispatched[0]["new_stage"] == "reativacao"
        assert "fluxo_reativacao_iniciado" in events_dispatched[0]["actions_triggered"]

@pytest.mark.asyncio
async def test_llm_orchestrated_synthesis():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/orchestrator/message", json={
            "phone": "5511933334444",
            "message": "Qual é a localização da clínica?",
            "patient_name": "Juliana Lima"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["detected_intent"] == "localizacao"
        assert "enviar_localizacao" in data["tools_executed"]
        assert "Paulista" in data["ai_response"]
