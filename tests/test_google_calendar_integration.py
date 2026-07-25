import asyncio
from datetime import datetime, timedelta

import pytest
from unittest.mock import patch

from app.services.validador_fluxo import processar_fluxo_atendimento
from app.services.google_calendar_service import calendar_service


def test_cria_evento_no_google_calendar_com_mock(monkeypatch):
    # Simula calendário habilitado e responses de API
    monkeypatch.setattr(calendar_service, "enabled", True)
    mock_event = {"id": "evento-123", "summary": "Teste"}

    with patch.object(calendar_service, "criar_evento", return_value=mock_event) as criar_evento_mock:
        # Dados de sessão já preparados para avançar na última etapa
        dados_sessao = {
            "nome": "Maria Silva",
            "sintoma": "Dor de cabeca",
            "convenio": "Unimed",
            "primeira_consulta": True,
            "preferencia_horario": "manha",
            "opcoes_horario": [
                {
                    "opcao": 1,
                    "horario_texto": "25/07/2026 09:00",
                    "inicio_iso": datetime(2026, 7, 25, 9, 0).isoformat(),
                    "fim_iso": (datetime(2026, 7, 25, 9, 0) + timedelta(minutes=30)).isoformat(),
                }
            ]
        }

        resposta, proximo_estado, dados_atualizados = asyncio.run(
            processar_fluxo_atendimento("aguardando_horario", "1", dados_sessao)
        )

        assert proximo_estado == "concluido"
        criar_evento_mock.assert_called_once()
        assert "Consulta Agendada" in resposta
        assert dados_atualizados["horario"] == "25/07/2026 09:00"
