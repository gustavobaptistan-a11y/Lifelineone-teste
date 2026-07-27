import json
from unittest.mock import MagicMock

from app.services.llm_service import LLMService


def test_extract_structured_desabilitado_retorna_vazio():
    service = LLMService.__new__(LLMService)
    service.enabled = False
    service.model = "gpt-4o-mini"
    service._client = None

    resultado = service.extract_structured("aguardando_nome", "Maria Silva")

    assert resultado == {"dados_extraidos": {}, "urgente": False}


def test_extract_structured_valida_resposta_openai():
    service = LLMService.__new__(LLMService)
    service.enabled = True
    service.model = "gpt-4o-mini"

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content=json.dumps(
                    {
                        "dados_extraidos": {
                            "nome": "Maria Silva",
                            "sintoma": "Dor de cabeca",
                        },
                        "urgente": False,
                    }
                )
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response
    service._client = mock_client

    resultado = service.extract_structured("aguardando_nome", "Me chamo Maria Silva")

    assert resultado["dados_extraidos"]["nome"] == "Maria Silva"
    assert resultado["urgente"] is False
    mock_client.chat.completions.create.assert_called_once()


def test_extract_structured_json_invalido_usa_fallback():
    service = LLMService.__new__(LLMService)
    service.enabled = True
    service.model = "gpt-4o-mini"

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="nao e json"))]
    mock_client.chat.completions.create.return_value = mock_response
    service._client = mock_client

    resultado = service.extract_structured("aguardando_nome", "Maria Silva")

    assert resultado == {"dados_extraidos": {}, "urgente": False}


def test_llm_service_instancia_global_tem_extract_structured():
    from app.services.llm_service import llm_service

    assert hasattr(llm_service, "extract_structured")
