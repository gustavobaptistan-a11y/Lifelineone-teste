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
async def test_exam_upload_and_multimodal_ocr():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Criar paciente
        res_p = await ac.post("/api/v1/patients/", json={
            "name": "Gustavo Exames",
            "phone": "5511944443333"
        })
        assert res_p.status_code == 201
        patient_id = res_p.json()["patient_id"]

        # 2. Enviar exame para análise de IA
        upload_payload = {
            "file_name": "espirometria_gustavo.pdf",
            "exam_type": "Espirometria"
        }
        res_upload = await ac.post(f"/api/v1/exams/upload/{patient_id}", json=upload_payload)
        assert res_upload.status_code == 200, res_upload.text
        data_upload = res_upload.json()

        assert data_upload["patient_id"] == patient_id
        assert "VEF1/CVF" in data_upload["extracted_findings"]
        assert data_upload["event_triggered"]["new_stage"] == "exames"

        # 3. Consultar Prontuário Eletrônico (PEP) do paciente
        res_history = await ac.get(f"/api/v1/exams/patient/{patient_id}")
        assert res_history.status_code == 200
        docs = res_history.json()
        assert len(docs) == 1
        assert docs[0]["file_name"] == "espirometria_gustavo.pdf"
        assert docs[0]["exam_type"] == "Espirometria"
