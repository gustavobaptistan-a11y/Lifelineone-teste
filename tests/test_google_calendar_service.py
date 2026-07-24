from datetime import datetime

import pytest

from app.services.google_calendar_service import GoogleCalendarService


def test_google_calendar_desabilitado_por_padrao(monkeypatch):
    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CALENDAR_ENABLED",
        False,
    )
    service = GoogleCalendarService()

    with pytest.raises(RuntimeError, match="desabilitado"):
        service.listar_eventos(datetime(2026, 7, 24), datetime(2026, 7, 25))


def test_google_calendar_nao_abre_autorizacao_sem_credencial(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CALENDAR_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.google_calendar_service.settings.GOOGLE_CREDENTIALS_FILE",
        str(tmp_path / "missing.json"),
    )
    service = GoogleCalendarService()

    with pytest.raises(FileNotFoundError, match="Credencial Google nao encontrada"):
        service.listar_eventos(datetime(2026, 7, 24), datetime(2026, 7, 25))
