import logging
import re
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncpg

from app.config import settings
from app.services.clinic_config import clinic_schedule_config
from app.services.google_calendar_service import calendar_service
from app.services import schedule_repository

logger = logging.getLogger(__name__)

PALAVRAS_CHAVE_URGENCIA = [
    "dor no peito",
    "falta de ar",
    "sangramento intenso",
    "desmaio",
    "perda de consciência",
    "convulsão",
    "dor muito forte",
    "pensamento suicida",
    "emergência"
]

def verificar_urgencia(texto: str) -> bool:
    texto_lower = _normalizar_texto(texto)
    for termo in PALAVRAS_CHAVE_URGENCIA:
        if _normalizar_texto(termo) in texto_lower:
            return True
    return False


def _normalizar_texto(texto: str) -> str:
    texto_sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caractere)
    )
    return " ".join(texto_sem_acentos.lower().split())


def _resposta_primeira_consulta(texto: str) -> bool | None:
    texto_normalizado = _normalizar_texto(texto)
    if re.search(r"\b(sim|s|primeira)\b", texto_normalizado):
        return True
    if re.search(r"\b(nao|n|retorno|ja sou paciente)\b", texto_normalizado):
        return False
    return None


def _resposta_convenio_valida(texto: str) -> bool:
    texto_normalizado = _normalizar_texto(texto)
    if not texto_normalizado or texto_normalizado in {"sim", "nao", "n", "s"}:
        return False
    return "particular" in texto_normalizado or len(texto_normalizado) >= 3


def _periodo_valido(texto: str) -> str | None:
    texto_normalizado = _normalizar_texto(texto)
    if re.search(r"\b(manha|matutino)\b", texto_normalizado):
        return "manha"
    if re.search(r"\b(tarde|vespertino)\b", texto_normalizado):
        return "tarde"
    return None


def _horario_valido(texto: str) -> bool:
    texto_normalizado = _normalizar_texto(texto)
    return bool(re.fullmatch(r"[12]", texto_normalizado)) or bool(
        re.search(r"\b(09:00|14:00)\b", texto_normalizado)
    )


async def _reservar_slot_db(slot_db_id: int, paciente: str) -> bool:
    if not settings.DATABASE_URL:
        return False

    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        reservado = await schedule_repository.reserve_slot(conn, slot_db_id, paciente)
        await conn.close()
        return reservado
    except Exception:
        logger.exception("Erro ao reservar slot no banco de dados")
        return False


def _parse_datetime(value: str) -> datetime:
    normalized = value
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized)


def _parse_event_datetime(event_time: dict | str) -> datetime:
    if isinstance(event_time, dict):
        raw_value = event_time.get("dateTime") or event_time.get("date")
    else:
        raw_value = event_time
    return _parse_datetime(raw_value)


def _obter_eventos_calendario(inicio: datetime, fim: datetime) -> list[dict]:
    try:
        return calendar_service.listar_eventos(inicio, fim)
    except Exception:
        logger.warning(
            "Não foi possível obter eventos do Google Calendar; usando disponibilidade local"
        )
        return []


def _slot_disponivel(eventos: list[dict], inicio: datetime, fim: datetime) -> bool:
    for evento in eventos:
        evento_inicio = _parse_event_datetime(evento["start"])
        evento_fim = _parse_event_datetime(evento["end"])
        if not (evento_fim <= inicio or evento_inicio >= fim):
            return False
    return True


async def _obter_horarios_disponiveis(periodo: str, limite: int = 3) -> list[dict]:
    if periodo not in {"manha", "tarde"}:
        return []

    timezone = ZoneInfo(clinic_schedule_config.calendar.timezone)
    inicio_busca = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    fim_busca = inicio_busca + timedelta(days=clinic_schedule_config.availability.search_days)

    opcoes = []

    # Tenta obter opções de slots do banco de dados local primeiro
    if settings.DATABASE_URL:
        try:
            conn = await asyncpg.connect(settings.DATABASE_URL)
            opcoes_db = await schedule_repository.formatar_opcoes_horarios(conn, periodo)
            await conn.close()
            for opcao in opcoes_db:
                data = datetime.strptime(opcao["horario_texto"], "%d/%m/%Y %H:%M")
                data = data.replace(tzinfo=timezone)
                termino = data + timedelta(minutes=clinic_schedule_config.appointment.duration_minutes)
                opcoes.append(
                    {
                        "opcao": opcao["opcao"],
                        "db_id": opcao.get("db_id"),
                        "horario_texto": opcao["horario_texto"],
                        "inicio_iso": data.isoformat(),
                        "fim_iso": termino.isoformat(),
                    }
                )
            if opcoes:
                return opcoes
        except Exception:
            logger.warning("Erro ao obter horários do banco de dados local; usando disponibilidade de calendário alternativa")

    eventos = _obter_eventos_calendario(inicio_busca, fim_busca)

    duracao = timedelta(minutes=clinic_schedule_config.appointment.duration_minutes)
    intervalo = duracao + timedelta(minutes=clinic_schedule_config.appointment.buffer_minutes)

    opcoes = []
    for dia_offset in range(clinic_schedule_config.availability.search_days):
        dia_corrente = inicio_busca + timedelta(days=dia_offset)
        dia_da_semana = dia_corrente.strftime("%A").lower()
        janelas = clinic_schedule_config.availability.weekly_hours.get(dia_da_semana, [])

        for janela in janelas:
            inicio_janela = datetime.combine(dia_corrente.date(), janela.start, tzinfo=timezone)
            fim_janela = datetime.combine(dia_corrente.date(), janela.end, tzinfo=timezone)
            horario_atual = inicio_janela

            while horario_atual + duracao <= fim_janela:
                if periodo == "manha" and horario_atual.hour >= 12:
                    break
                if periodo == "tarde" and horario_atual.hour < 12:
                    horario_atual += intervalo
                    continue

                termino = horario_atual + duracao
                if _slot_disponivel(eventos, horario_atual, termino):
                    opcoes.append(
                        {
                            "opcao": len(opcoes) + 1,
                            "horario_texto": horario_atual.strftime("%d/%m/%Y %H:%M"),
                            "inicio_iso": horario_atual.isoformat(),
                            "fim_iso": termino.isoformat(),
                        }
                    )
                    if len(opcoes) >= limite:
                        return opcoes

                horario_atual += intervalo

    return opcoes


def _formatar_opcoes_horario(opcoes: list[dict]) -> str:
    return "\n".join(
        f"{opcao['opcao']}️⃣ {opcao['horario_texto']}" for opcao in opcoes
    )


async def processar_fluxo_atendimento(estado_atual: str, texto_usuario: str, dados_sessao: dict) -> tuple:
    # 0. Interceptação crítica de urgência
    if verificar_urgencia(texto_usuario):
        resposta_emergencia = (
            "⚠️ **ATENÇÃO: Identificamos um possível caso de urgência médica.**\n\n"
            "Por favor, procure o pronto-socorro mais próximo ou ligue imediatamente para o **SAMU (192)**. "
            "Este canal automatizado não substitui o atendimento médico de emergência."
        )
        return resposta_emergencia, "urgencia_detectada", dados_sessao

    texto = texto_usuario.strip()
    proximo_estado = estado_atual

    # Máquina de Estados da Jornada do Paciente
    if estado_atual == "inicio":
        resposta = "Olá! Bem-vindo ao sistema de atendimento. Para começarmos, qual é o seu **nome completo**?"
        proximo_estado = "aguardando_nome"

    elif estado_atual == "aguardando_nome":
        if len(texto.split()) < 2:
            return "Por favor, informe seu **nome completo** para continuarmos.", estado_atual, dados_sessao
        dados_sessao["nome"] = texto
        resposta = f"Obrigado, {texto}. Qual é o principal **sintoma ou motivo** da sua consulta?"
        proximo_estado = "aguardando_sintoma"

    elif estado_atual == "aguardando_sintoma":
        if len(texto) < 3:
            return "Pode descrever brevemente o **motivo ou sintoma** da consulta?", estado_atual, dados_sessao
        dados_sessao["sintoma"] = texto
        resposta = "Qual é o seu **convênio médico** (ou se prefere atendimento particular)?"
        proximo_estado = "aguardando_convenio"

    elif estado_atual == "aguardando_convenio":
        if not _resposta_convenio_valida(texto):
            return "Informe se o atendimento será **particular** ou qual é o seu **convênio**.", estado_atual, dados_sessao
        dados_sessao["convenio"] = texto
        resposta = "Esta é a sua **primeira consulta** conosco? (Responda Sim ou Não)"
        proximo_estado = "aguardando_primeira_consulta"

    elif estado_atual == "aguardando_primeira_consulta":
        primeira_consulta = _resposta_primeira_consulta(texto)
        if primeira_consulta is None:
            return "Por favor, responda se é sua **primeira consulta** ou se é um **retorno**.", estado_atual, dados_sessao
        dados_sessao["primeira_consulta"] = primeira_consulta
        resposta = "Qual período você prefere: **manhã** ou **tarde**?"
        proximo_estado = "aguardando_preferencia_horario"

    elif estado_atual == "aguardando_preferencia_horario":
        periodo = _periodo_valido(texto)
        if periodo is None:
            return "Informe sua preferência de período: **manhã** ou **tarde**.", estado_atual, dados_sessao

        opcoes = await _obter_horarios_disponiveis(periodo)
        if not opcoes:
            return (
                "Desculpe, não encontrei horários disponíveis para esse período nos próximos dias. "
                "Por favor, tente outro período ou tente novamente mais tarde.",
                estado_atual,
                dados_sessao,
            )

        dados_sessao["preferencia_horario"] = periodo
        dados_sessao["opcoes_horario"] = opcoes
        resposta = (
            f"Perfeito. Tenho os seguintes horários disponíveis para {periodo}:\n\n"
            f"{_formatar_opcoes_horario(opcoes)}\n\n"
            "Digite o número da opção desejada:"
        )
        proximo_estado = "aguardando_horario"

    elif estado_atual == "aguardando_horario":
        opcoes_horario = dados_sessao.get("opcoes_horario", [])
        if not opcoes_horario:
            return (
                "Ocorreu um erro ao recuperar as opções de horário. Por favor, digite manhã ou tarde novamente.",
                "aguardando_preferencia_horario",
                dados_sessao,
            )

        escolha = None
        selected = None
        if texto.isdigit():
            escolha = int(texto)
            for opcao in opcoes_horario:
                if opcao["opcao"] == escolha:
                    selected = opcao
                    break
        else:
            texto_normalizado = _normalizar_texto(texto)
            selected = next(
                (
                    opcao
                    for opcao in opcoes_horario
                    if texto_normalizado in _normalizar_texto(opcao["horario_texto"])
                ),
                None,
            )

        if selected is None:
            return (
                "Escolha uma opção válida entre os horários apresentados.",
                estado_atual,
                dados_sessao,
            )

        if selected.get("db_id") is not None:
            reservado = await _reservar_slot_db(selected["db_id"], dados_sessao.get("nome", "Paciente"))
            if not reservado:
                dados_sessao.pop("opcoes_horario", None)
                return (
                    "O horário escolhido acabou de ser reservado por outra pessoa. Por favor, escolha outro período.",
                    "aguardando_preferencia_horario",
                    dados_sessao,
                )
            dados_sessao["slot_db_id"] = selected["db_id"]

        dados_sessao["horario"] = selected["horario_texto"]
        dados_sessao["horario_inicio_iso"] = selected["inicio_iso"]
        dados_sessao["horario_fim_iso"] = selected["fim_iso"]

        if calendar_service.enabled:
            try:
                inicio_evento = _parse_datetime(selected["inicio_iso"])
                fim_evento = _parse_datetime(selected["fim_iso"])
                nome = dados_sessao.get("nome", "Paciente")
                descricao = (
                    f"Paciente: {nome}\n"
                    f"Convênio: {dados_sessao.get('convenio', 'Particular')}\n"
                    f"Sintoma: {dados_sessao.get('sintoma', 'Não informado')}\n"
                    f"Primeira consulta: {dados_sessao.get('primeira_consulta', False)}"
                )
                calendar_service.criar_evento(
                    f"Consulta LifelineOne - {nome}",
                    inicio_evento,
                    fim_evento,
                    descricao,
                )
            except Exception:
                logger.exception("Falha ao criar evento no Google Calendar")
                return (
                    "Ocorreu um erro ao reservar o horário no Google Calendar. Tente novamente mais tarde.",
                    estado_atual,
                    dados_sessao,
                )

        nome = dados_sessao.get("nome", "Paciente")
        convenio = dados_sessao.get("convenio", "Particular")
        horario = dados_sessao.get("horario", texto)
        resposta = (
            f"✅ **Consulta Agendada com Sucesso!**\n\n"
            f"Resumo:\n- Nome: {nome}\n- Convênio: {convenio}\n- Horário: {horario}\n\n"
            "Te aguardamos na clínica!"
        )
        proximo_estado = "concluido"

    else:
        resposta = "Seu atendimento já foi concluído. Caso precise de novo agendamento, digite 'olá'."
        proximo_estado = "inicio"

    return resposta, proximo_estado, dados_sessao
