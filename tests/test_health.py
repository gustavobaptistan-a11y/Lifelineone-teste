from fastapi.testclient import TestClient

from app.config import settings
from main import app


def test_health_does_not_expose_secret_values(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "secret-openai")
    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "secret-evolution")
    monkeypatch.setattr(settings, "EVOLUTION_INSTANCE_NAME", "test-instance")
    monkeypatch.setattr(settings, "EVOLUTION_SEND_ENABLED", True)
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://user:pass@example/db")
    monkeypatch.setattr(settings, "GOOGLE_CREDENTIALS_FILE", "secret-path.json")
    monkeypatch.setattr(settings, "GOOGLE_TOKEN_FILE", "secret-token.json")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["integrations"]["openai"] == {"configured": True}
    assert data["integrations"]["database"] == {"configured": True}
    assert data["integrations"]["evolution"]["configured"] is True
    assert data["integrations"]["evolution"]["ready_for_send"] is True
    assert "secret-openai" not in response.text
    assert "secret-evolution" not in response.text
    assert "secret-path.json" not in response.text
    assert "secret-token.json" not in response.text
    assert "postgresql://" not in response.text


def test_health_reports_evolution_not_ready_when_send_disabled(monkeypatch):
    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "secret-evolution")
    monkeypatch.setattr(settings, "EVOLUTION_INSTANCE_NAME", "test-instance")
    monkeypatch.setattr(settings, "EVOLUTION_SEND_ENABLED", False)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["integrations"]["evolution"]["configured"] is True
    assert data["integrations"]["evolution"]["send_enabled"] is False
    assert data["integrations"]["evolution"]["ready_for_send"] is False
