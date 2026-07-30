from fastapi.testclient import TestClient

from app.config import settings
from main import app


def test_health_does_not_expose_secret_values(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "secret-openai")
    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "secret-evolution")
    monkeypatch.setattr(settings, "EVOLUTION_INSTANCE_NAME", "test-instance")
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://user:pass@example/db")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["integrations"]["openai"] == {"configured": True}
    assert data["integrations"]["database"] == {"configured": True}
    assert data["integrations"]["evolution"]["configured"] is True
    assert "secret-openai" not in response.text
    assert "secret-evolution" not in response.text
    assert "postgresql://" not in response.text