from pathlib import Path

import pytest

from app.services.clinic_config import load_clinic_config


CONFIG_PATH = Path(__file__).parents[1] / "config" / "clinic.yaml"


def test_configuracao_padrao_da_clinica():
    config = load_clinic_config(CONFIG_PATH)

    assert config.calendar.id == "primary"
    assert config.calendar.timezone == "America/Sao_Paulo"
    assert config.appointment.duration_minutes == 30
    assert config.appointment.buffer_minutes == 10
    assert config.appointment.minimum_notice_hours == 2
    assert config.availability.max_options == 3
    assert config.availability.search_days == 30
    assert len(config.availability.weekly_hours["monday"]) == 2
    assert config.availability.weekly_hours["sunday"] == []


def test_configuracao_rejeita_janela_invertida(tmp_path):
    config_path = tmp_path / "clinic.yaml"
    config_path.write_text(
        """
calendar:
  id: primary
  timezone: America/Sao_Paulo
appointment:
  duration_minutes: 30
  buffer_minutes: 10
  minimum_notice_hours: 2
availability:
  max_options: 3
  search_days: 30
  weekly_hours:
    monday:
      - start: '18:00'
        end: '08:00'
    tuesday: []
    wednesday: []
    thursday: []
    friday: []
    saturday: []
    sunday: []
conflicts: {}
exceptions: {}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="start deve ser anterior"):
        load_clinic_config(config_path)
