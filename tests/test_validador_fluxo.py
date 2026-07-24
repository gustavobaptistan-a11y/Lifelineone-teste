import asyncio

from app.services.validador_fluxo import processar_fluxo_atendimento, verificar_urgencia


def processar(estado, texto, dados=None):
    return asyncio.run(processar_fluxo_atendimento(estado, texto, dados or {}))


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


def test_nome_incompleto_nao_avanca():
    resposta, estado, dados = processar("aguardando_nome", "Maria")

    assert estado == "aguardando_nome"
    assert "nome completo" in resposta
    assert dados == {}