import os

from fastapi.testclient import TestClient
from main import app


def test_dashboard_route_exists():
    os.environ["PYTHONPATH"] = "."
    client = TestClient(app)
    response = client.get("/dashboard")

    assert response.status_code in {200, 500}
    assert "Dashboard Lifeline" in response.text
