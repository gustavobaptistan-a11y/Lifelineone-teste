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
async def test_websocket_live_broadcast():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Criar paciente primeiro
        res_p = await ac.post("/api/v1/patients/", json={
            "name": "Paciente WebSocket",
            "phone": "5511933332222"
        })
        assert res_p.status_code == 201
        patient_id = res_p.json()["patient_id"]

        # 2. Disparar evento para testar transmissão ao vivo
        res_ev = await ac.post("/api/v1/events/publish", json={
            "event_type": "pagamento_confirmado",
            "patient_id": patient_id,
            "data": {"amount": "R$ 500,00"}
        })
        assert res_ev.status_code == 200, res_ev.text
        data = res_ev.json()
        assert data["event_type"] == "pagamento_confirmado"
        assert data["new_stage"] == "tratamento"
