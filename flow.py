import re
from typing import Any, Callable, Optional

from app.db import buscar_horarios_disponiveis, reservar_horario_db
from app.models import SessaoPaciente
from app.text_utils import normalizar_texto


def selecionar_opcao_horario(texto: str, opcoes: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    texto_normalizado = normalizar_texto(texto)
    match = re.search(r"\b([1-3])\b", texto_normalizado)
    if match:
        indice = int(match.group(1)) - 1
        if 0 <= indice < len(opcoes):
            return opcoes[indice]
    for opcao in opcoes:
        if normalizar_texto(opcao["horario"]) in texto_normalizado:
            return opcao
    return None


def resposta_opcoes(opcoes: list[dict[str, Any]]) -> str:
    if not opcoes:
        return (
            "No momento nao encontrei horarios disponiveis nesse periodo. "
            "Voce prefere ver outro periodo ou quer que a clinica entre em contato?"
        )
    linhas = [f"{idx}. {opcao['horario']}" for idx, opcao in enumerate(opcoes, start=1)]
    return "Encontrei estes horarios disponiveis:\n" + "\n".join(linhas) + "\nQual opcao voce prefere?"


def _handle_coletar_nome(sessao: SessaoPaciente, texto_limpo: str, texto_normalizado: str) -> str:
    if len(texto_limpo.split()) < 2 or any(char.isdigit() for char in texto_limpo):
        return "Por favor, me informe seu nome completo."
    sessao.dados.nome = texto_limpo.title()
    sessao.etapa = "coletar_motivo"
    return f"Prazer, {sessao.dados.nome.split()[0]}. Me conte rapidamente o motivo da consulta."


def _handle_coletar_motivo(sessao: SessaoPaciente, texto_limpo: str, texto_normalizado: str) -> str:
    if len(texto_limpo) < 5:
        return "Pode me explicar em uma frase o motivo da consulta?"
    sessao.dados.motivo = texto_limpo
    sessao.etapa = "coletar_convenio"
    return "Entendi. Voce e particular ou tem convenio? Se tiver convenio, qual e?"


def _handle_coletar_convenio(sessao: SessaoPaciente, texto_limpo: str, texto_normalizado: str) -> str:
    if len(texto_limpo) < 3:
        return "Voce sera atendido como particular ou por convenio? Se for convenio, me diga qual."
    sessao.dados.convenio = texto_limpo
    sessao.etapa = "coletar_status_paciente"
    return "Certo. Voce ja e paciente da clinica ou esta sera a primeira consulta?"


def _handle_coletar_status_paciente(sessao: SessaoPaciente, texto_limpo: str, texto_normalizado: str) -> str:
    termos_validos = ["ja", "sou", "primeira", "novo", "nova", "nunca"]
    if not any(palavra in texto_normalizado for palavra in termos_validos):
        return "Voce ja e paciente da clinica ou esta sera a primeira consulta?"
    sessao.dados.status_paciente = texto_limpo
    sessao.etapa = "coletar_preferencia"
    return "Perfeito. Voce prefere atendimento de manha ou a tarde? Se tiver um dia melhor, pode me dizer tambem."


def _handle_coletar_preferencia(sessao: SessaoPaciente, texto_limpo: str, texto_normalizado: str) -> str:
    if "manha" not in texto_normalizado and "tarde" not in texto_normalizado:
        return "Voce prefere atendimento de manha ou a tarde?"
    sessao.dados.preferencia_horario = texto_limpo
    sessao.opcoes_oferecidas = buscar_horarios_disponiveis(texto_limpo)
    sessao.etapa = "escolher_horario"
    return resposta_opcoes(sessao.opcoes_oferecidas)


def _handle_escolher_horario(sessao: SessaoPaciente, texto_limpo: str, texto_normalizado: str) -> str:
    if any(palavra in texto_normalizado for palavra in ["mais", "outras", "outros", "nao serve", "nao posso"]):
        sessao.opcoes_oferecidas = buscar_horarios_disponiveis(sessao.dados.preferencia_horario, offset=3)
        return resposta_opcoes(sessao.opcoes_oferecidas)
    opcao = selecionar_opcao_horario(texto_limpo, sessao.opcoes_oferecidas)
    if not opcao:
        return "Pode escolher pelo numero da opcao ou repetir o horario desejado."
    horario_reservado = reservar_horario_db(opcao["id"], sessao.dados)
    if not horario_reservado:
        sessao.opcoes_oferecidas = buscar_horarios_disponiveis(sessao.dados.preferencia_horario)
        return "Esse horario acabou de ficar indisponivel. Vou te mostrar as opcoes atuais.\n" + resposta_opcoes(sessao.opcoes_oferecidas)
    sessao.etapa = "agendamento_confirmado"
    return f"Agendamento confirmado para {sessao.dados.nome}, em {horario_reservado}. Por favor, chegue com 10 minutos de antecedencia."


def _handle_agendamento_confirmado(sessao: SessaoPaciente, texto_limpo: str, texto_normalizado: str) -> str:
    return "Seu agendamento ja foi confirmado. Se precisar alterar, a clinica pode te ajudar."


etapas_handler: dict[str, Callable[[SessaoPaciente, str, str], str]] = {
    "coletar_nome": _handle_coletar_nome,
    "coletar_motivo": _handle_coletar_motivo,
    "coletar_convenio": _handle_coletar_convenio,
    "coletar_status_paciente": _handle_coletar_status_paciente,
    "coletar_preferencia": _handle_coletar_preferencia,
    "escolher_horario": _handle_escolher_horario,
    "agendamento_confirmado": _handle_agendamento_confirmado,
}


def validar_e_atualizar_sessao(sessao: SessaoPaciente, texto: str) -> str:
    texto_limpo = texto.strip()
    texto_normalizado = normalizar_texto(texto_limpo)

    handler = etapas_handler.get(sessao.etapa)
    if handler:
        return handler(sessao, texto_limpo, texto_normalizado)

    return "Desculpe, nao entendi em que parte do agendamento estamos. Poderia recomecar?"
