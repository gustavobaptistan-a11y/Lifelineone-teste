import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_whatsapp_webhook_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/webhooks/whatsapp",
            json={
                "phone_number": "5511999887766",
                "sender_name": "Gustavo",
                "message_text": "ola meu nome é Gustavo, gostaria de agendar consulta para amanhã"
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "processed"
        assert data["patient_name"] == "Gustavo"
        assert "response" in data
