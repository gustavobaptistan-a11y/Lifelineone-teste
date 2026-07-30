import asyncio
from unittest.mock import MagicMock

import app.services.validador_fluxo as validador_fluxo
from app.services.validador_fluxo import processar_fluxo_atendimento, verificar_urgencia


def processar(estado, texto, dados=None, remote_jid=None):
    return asyncio.run(processar_fluxo_atendimento(estado, texto, dados or {}, remote_jid=remote_jid))

async def processar_async(estado, texto, dados=None, remote_jid=None):
    return await processar_fluxo_atendimento(estado, texto, dados or {}, remote_jid=remote_jid)


def test_fluxo_utiliza_dados_extraidos_do_llm(monkeypatch):
    llm_stub = MagicMock()
    llm_stub.enabled = True
    llm_stub.extract_structured.return_value = {
        "dados_extraidos": {"nome": "Maria Silva"},
        "urgente": False,
    }
    monkeypatch.setattr(validador_fluxo, "llm_service", llm_stub)

    resposta, estado, dados = processar("aguardando_nome", "Maria Silva")

    assert estado == "aguardando_sintoma"
    assert dados["nome"] == "Maria Silva"
    llm_stub.extract_structured.assert_called_once_with("aguardando_nome", "Maria Silva")


def test_fluxo_interrompe_por_urgencia_via_llm(monkeypatch):
    llm_stub = MagicMock()
    llm_stub.enabled = True
    llm_stub.extract_structured.return_value = {
        "dados_extraidos": {},
        "urgente": True,
    }
    monkeypatch.setattr(validador_fluxo, "llm_service", llm_stub)
    alerta_stub = MagicMock()
    monkeypatch.setattr(validador_fluxo.alert_service, "notificar_urgencia", alerta_stub)

    resposta, estado, dados = processar(
        "aguardando_nome",
        "Estou muito mal e nao consigo explicar",
        remote_jid="paciente@s.whatsapp.net",
    )

    assert estado == "urgencia_detectada"
    assert "SAMU" in resposta
    assert dados == {}
    alerta_stub.assert_called_once_with(
        "paciente@s.whatsapp.net",
        "Estou muito mal e nao consigo explicar",
        {},
        origem="llm",
    )


def test_fluxo_notifica_humano_em_urgencia_deterministica(monkeypatch):
    alerta_stub = MagicMock()
    monkeypatch.setattr(validador_fluxo.alert_service, "notificar_urgencia", alerta_stub)

    resposta, estado, dados = processar(
        "aguardando_nome",
        "Estou sentindo dor no peito",
        {"nome": "Maria Silva"},
        remote_jid="paciente@s.whatsapp.net",
    )

    assert estado == "urgencia_detectada"
    assert "SAMU" in resposta
    alerta_stub.assert_called_once_with(
        "paciente@s.whatsapp.net",
        "Estou sentindo dor no peito",
        {"nome": "Maria Silva"},
        origem="deterministica",
    )


def test_urgencia_com_acentuacao_e_interceptada():
    assert verificar_urgencia("Estou com falta de ar")
    assert verificar_urgencia("Estou com uma convulsao")


def test_resposta_invalida_repete_pergunta_sem_avancar():
    resposta, estado, dados = processar("aguardando_primeira_consulta", "talvez")

    assert estado == "aguardando_primeira_consulta"
    assert "primeira consulta" in resposta
    assert dados == {}


def test_fluxo_valido_coleta_preferencia_antes_do_horario():
    dados = {}
    _, estado, dados = processar("inicio", "Ola", dados)
    _, estado, dados = processar(estado, "Maria Silva", dados)
    _, estado, dados = processar(estado, "Dor de cabeca", dados)
    _, estado, dados = processar(estado, "Unimed", dados)
    _, estado, dados = processar(estado, "Sim", dados)

    assert estado == "aguardando_preferencia_horario"
    _, estado, dados = processar(estado, "manha", dados)
    assert estado == "aguardando_horario"
    _, estado, dados = processar(estado, "1", dados)

    assert estado == "concluido"
    assert dados["preferencia_horario"] == "manha"
    assert dados["primeira_consulta"] is True
    assert dados["convenio"] == "Unimed"


def test_paciente_cadastrado_saudacao_avanca_para_sintoma(monkeypatch):
    agendamento_stub = {
        "paciente": {"nome_completo": "Maria Silva"},
    }
    async def buscar_ultimo_agendamento_confirmado_async(remote_jid):
        return agendamento_stub

    monkeypatch.setattr(
        validador_fluxo.agendamento_repository,
        "buscar_ultimo_agendamento_confirmado_async",
        buscar_ultimo_agendamento_confirmado_async,
    )

    resposta, estado, dados = asyncio.run(
        processar_fluxo_atendimento(
            "inicio",
            "Olá",
            {},
            remote_jid="5511999999999@c.us",
        )
    )

    assert estado == "aguardando_sintoma"
    assert "Olá Maria Silva" in resposta
    assert dados["nome"] == "Maria Silva"
    assert dados["paciente_cadastrado"] is True


def test_nome_incompleto_nao_avanca():
    resposta, estado, dados = processar("aguardando_nome", "Maria")

    assert estado == "aguardando_nome"
    assert "nome completo" in resposta
    assert dados == {}


def test_nome_e_normalizado_antes_de_salvar():
    resposta, estado, dados = processar("aguardando_nome", "gustavo henrique")

    assert estado == "aguardando_sintoma"
    assert dados["nome"] == "Gustavo Henrique"
    assert "Gustavo Henrique" in resposta


def test_convenio_generico_nao_avanca():
    resposta, estado, dados = processar("aguardando_convenio", "convênio")

    assert estado == "aguardando_convenio"
    assert "nome do seu" in resposta
    assert dados == {}


def test_confirmacao_final_orienta_antecedencia_e_documento():
    dados = {}
    _, estado, dados = processar("inicio", "Ola", dados)
    _, estado, dados = processar(estado, "Maria Silva", dados)
    _, estado, dados = processar(estado, "Dor de cabeca", dados)
    _, estado, dados = processar(estado, "Particular", dados)
    _, estado, dados = processar(estado, "Sim", dados)
    _, estado, dados = processar(estado, "manha", dados)
    resposta, estado, dados = processar(estado, "1", dados)

    assert estado == "concluido"
    assert "10 minutos" in resposta
    assert "documento com foto" in resposta
    assert "carteirinha" not in resposta.lower()


def test_gera_horarios_disponiveis_sem_google_calendar():
    dados = {}
    _, estado, dados = processar("inicio", "Ola", dados)
    _, estado, dados = processar(estado, "Maria Silva", dados)
    _, estado, dados = processar(estado, "Dor de cabeca", dados)
    _, estado, dados = processar(estado, "Unimed", dados)
    _, estado, dados = processar(estado, "Sim", dados)

    assert estado == "aguardando_preferencia_horario"
    _, estado, dados = processar(estado, "manha", dados)

    assert estado == "aguardando_horario"
    assert isinstance(dados.get("opcoes_horario"), list)
    assert len(dados["opcoes_horario"]) >= 1
