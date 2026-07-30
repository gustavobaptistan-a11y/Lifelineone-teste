from datetime import datetime
from pathlib import Path

import pytest

from app.services.google_calendar_service import GoogleCalendarService


ARTIFACTS_DIR = Path(__file__).parents[1] / ".test_artifacts" / "google_calendar"


def test_google_calendar_desabilitado_por_padrao(monkeypatch):
    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CALENDAR_ENABLED",
        False,
    )
    service = GoogleCalendarService()

    with pytest.raises(RuntimeError, match="desabilitado"):
        service.listar_eventos(datetime(2026, 7, 24), datetime(2026, 7, 25))


def test_google_calendar_nao_abre_autorizacao_sem_credencial(monkeypatch):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    missing_credentials = ARTIFACTS_DIR / "missing.json"
    if missing_credentials.exists():
        missing_credentials.unlink()

    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CALENDAR_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CREDENTIALS_FILE",
        str(missing_credentials),
    )
    service = GoogleCalendarService()

    with pytest.raises(FileNotFoundError, match="Credencial Google nao encontrada"):
        service.listar_eventos(datetime(2026, 7, 24), datetime(2026, 7, 25))

def test_google_calendar_nao_abre_oauth_local_sem_flag(monkeypatch):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    credentials_file = ARTIFACTS_DIR / "oauth_client.json"
    credentials_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CALENDAR_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CALENDAR_ALLOW_LOCAL_AUTH",
        False,
    )
    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CREDENTIALS_FILE",
        str(credentials_file),
    )
    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_TOKEN_FILE",
        str(ARTIFACTS_DIR / "missing-token.json"),
    )
    service = GoogleCalendarService()

    with pytest.raises(RuntimeError, match="OAuth local"):
        service.listar_eventos(datetime(2026, 7, 24), datetime(2026, 7, 25))