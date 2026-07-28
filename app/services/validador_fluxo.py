import logging
import re
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncpg

from app.config import settings
from app.services.clinic_config import clinic_schedule_config
from app.services.google_calendar_service import calendar_service
from app.services.llm_service import llm_service
from app.services import schedule_repository
from app.services.agendamento_repository import agendamento_repository

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

SAUDACOES = {"ola", "olá", "oi", "bom dia", "boa tarde", "boa noite", "ei", "ola!", "oi!"}

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


def _eh_saudacao(texto: str) -> bool:
    txt = _normalizar_texto(texto)
    return any(txt == s for s in SAUDACOES)


def _eh_possivelmente_nome(texto: str) -> bool:
    """Heurística simples para aceitar nomes: 2-4 palavras, sem palavras indicativas de ação."""
    palavras = texto.strip().split()
    if len(palavras) < 2 or len(palavras) > 4:
        return False
    texto_normalizado = _normalizar_texto(texto)
    palavras_acao = {"quero", "agendar", "marcar", "consulta", "preciso", "ajuda"}
    if any(p in texto_normalizado for p in palavras_acao):
        return False
    # evitar frases com pontuação que indicam sentença
    if any(c in texto for c in ",.;:"):
        return False
    return True


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


def _resposta_afirmativa(texto: str) -> bool:
    texto_normalizado = _normalizar_texto(texto)
    return bool(re.search(r"\b(sim|s|claro|ok|certo|perfeito|confirmo)\b", texto_normalizado))


def _resposta_negativa(texto: str) -> bool:
    texto_normalizado = _normalizar_texto(texto)
    return bool(re.search(r"\b(n[ao]?|não|nao|errado|inadequado|mudou|alterou|outro)\b", texto_normalizado))


def _quer_reagendar(texto: str) -> bool:
    texto_normalizado = _normalizar_texto(texto)
    return bool(re.search(r"\b(alterar|mudar|remarcar|trocar|nao\s+est[ae] certo|não está certo|não|nao)\b", texto_normalizado))


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


def _parse_datetime(value: str, timezone: ZoneInfo | None = None) -> datetime:
    normalized = value
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    if "T" not in normalized:
        normalized = f"{normalized}T00:00:00"

    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone or ZoneInfo(clinic_schedule_config.calendar.timezone)
        )
    return parsed


def _parse_event_datetime(event_time: dict | str) -> datetime:
    if isinstance(event_time, dict):
        raw_value = event_time.get("dateTime") or event_time.get("date")
    else:
        raw_value = event_time
    timezone = ZoneInfo(clinic_schedule_config.calendar.timezone)
    return _parse_datetime(raw_value, timezone)


def _obter_eventos_calendario(inicio: datetime, fim: datetime) -> list[dict]:
    if not calendar_service.enabled:
        return []

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
    agora = datetime.now(timezone)
    inicio_busca = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_busca = inicio_busca + timedelta(days=clinic_schedule_config.availability.search_days)
    min_notice = timedelta(hours=clinic_schedule_config.appointment.minimum_notice_hours)
    disponivel_a_partir = agora + min_notice

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
                if horario_atual < disponivel_a_partir:
                    horario_atual += intervalo
                    continue
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


def _extrair_payload_llm(estado_atual: str, texto_usuario: str) -> dict:
    if not llm_service.enabled:
        return {"dados_extraidos": {}, "urgente": False}

    try:
        resultado = llm_service.extract_structured(estado_atual, texto_usuario)
    except Exception:
        logger.exception("Falha ao extrair dados do LLM; fallback para texto bruto do usuário.")
        return {
            "dados_extraidos": {"texto_bruto": texto_usuario},
            "urgente": False,
        }

    if not isinstance(resultado, dict):
        logger.warning("Resposta inválida do LLM; fallback para texto bruto do usuário.")
        return {
            "dados_extraidos": {"texto_bruto": texto_usuario},
            "urgente": False,
        }

    return {
        "dados_extraidos": resultado.get("dados_extraidos", {}) or {},
        "urgente": bool(resultado.get("urgente", False)),
    }


async def processar_fluxo_atendimento(
    estado_atual: str,
    texto_usuario: str,
    dados_sessao: dict,
    remote_jid: str | None = None,
) -> tuple:
    try:
        texto = texto_usuario.strip()
        if estado_atual == "inicio" and _eh_saudacao(texto):
            if remote_jid:
                agendamento_anterior = await agendamento_repository.buscar_ultimo_agendamento_confirmado_async(
                    remote_jid
                )
                if agendamento_anterior:
                    nome_paciente = (
                        agendamento_anterior.get("paciente", {}).get("nome_completo")
                        or agendamento_anterior.get("paciente", {}).get("nome")
                        or ""
                    )
                    saudacao_nome = f"Olá {nome_paciente}!" if nome_paciente else "Olá!"
                    dados_sessao["paciente_cadastrado"] = True
                    if nome_paciente:
                        dados_sessao["nome"] = nome_paciente
                    resposta = (
                        f"{saudacao_nome} Que bom te ver por aqui novamente. "
                        "Como posso te ajudar na sua consulta de hoje?"
                    )
                    return resposta, "aguardando_sintoma", dados_sessao

            resposta = (
                "Olá! 👋 Bem-vindo ao atendimento da Lifeline. Para eu te localizar, qual é o seu nome completo, por favor?"
            )
            return resposta, "aguardando_nome", dados_sessao

        # 0. Interceptação crítica de urgência
        if verificar_urgencia(texto_usuario):
            resposta_emergencia = (
                "⚠️ **ATENÇÃO: Identificamos um possível caso de urgência médica.**\n\n"
                "Por favor, procure o pronto-socorro mais próximo ou ligue imediatamente para o **SAMU (192)**. "
                "Este canal automatizado não substitui o atendimento médico de emergência."
            )
            return resposta_emergencia, "urgencia_detectada", dados_sessao

        dados_llm = _extrair_payload_llm(estado_atual, texto)
        if dados_llm.get("urgente"):
            resposta_emergencia = (
                "⚠️ **ATENÇÃO: Identificamos um possível caso de urgência médica.**\n\n"
                "Por favor, procure o pronto-socorro mais próximo ou ligue imediatamente para o **SAMU (192)**. "
                "Este canal automatizado não substitui o atendimento médico de emergência."
            )
            return resposta_emergencia, "urgencia_detectada", dados_sessao

        dados_extraidos_llm = dados_llm.get("dados_extraidos", {}) or {}
        proximo_estado = estado_atual

        # Máquina de Estados da Jornada do Paciente
        if estado_atual == "inicio":
            resposta = "Olá! 👋 Bem-vindo ao atendimento da Lifeline. Para eu te localizar, qual é o seu nome completo, por favor?"
            proximo_estado = "aguardando_nome"

        elif estado_atual == "aguardando_nome":
            nome_extraido = dados_extraidos_llm.get("nome", "").strip()
            nome = nome_extraido if nome_extraido else texto

            if _eh_saudacao(nome) or not _eh_possivelmente_nome(nome):
                return (
                    "Desculpe, não entendi — poderia informar seu nome completo (nome e sobrenome)?",
                    estado_atual,
                    dados_sessao,
                )

            dados_sessao["nome"] = nome
            resposta = (
                f"Obrigado, {nome}! Pra entender melhor, qual é o principal sintoma ou motivo da sua consulta?"
            )
            proximo_estado = "aguardando_sintoma"

        elif estado_atual == "aguardando_sintoma":
            sintoma_extraido = dados_extraidos_llm.get("sintoma", "").strip()
            sintoma = sintoma_extraido if sintoma_extraido else texto

            if len(sintoma) < 3:
                return (
                    "Poderia descrever brevemente o motivo ou sintoma? Uma frase é suficiente.",
                    estado_atual,
                    dados_sessao,
                )
            dados_sessao["sintoma"] = sintoma
            resposta = (
                "Entendi. Você irá pelo convênio ou prefere atendimento particular?"
            )
            proximo_estado = "aguardando_convenio"

        elif estado_atual == "aguardando_convenio":
            convenio_extraido = dados_extraidos_llm.get("convenio", "").strip()
            convenio = convenio_extraido if convenio_extraido else texto

            if not _resposta_convenio_valida(convenio):
                return (
                    "Pode me dizer se é atendimento **particular** ou qual é o nome do seu **convênio**?",
                    estado_atual,
                    dados_sessao,
                )
            dados_sessao["convenio"] = convenio
            resposta = "Perfeito. Esta é a sua primeira consulta conosco? (Responda Sim ou Não)"
            proximo_estado = "aguardando_primeira_consulta"

        elif estado_atual == "aguardando_primeira_consulta":
            primeira_consulta_extraida = dados_extraidos_llm.get("primeira_consulta", "").strip()
            primeira_consulta_valor = primeira_consulta_extraida if primeira_consulta_extraida else texto
            primeira_consulta = _resposta_primeira_consulta(primeira_consulta_valor)
            if primeira_consulta is None:
                return "Por favor, responda se é sua **primeira consulta** ou se é um **retorno**.", estado_atual, dados_sessao
            dados_sessao["primeira_consulta"] = primeira_consulta
            resposta = "Qual período você prefere: **manhã** ou **tarde**?"
            proximo_estado = "aguardando_preferencia_horario"

        elif estado_atual == "aguardando_preferencia_horario":
            periodo_extraido = dados_extraidos_llm.get("preferencia_periodo", "").strip()
            periodo_texto = periodo_extraido if periodo_extraido else texto
            periodo = _periodo_valido(periodo_texto)
            if periodo is None:
                return (
                    "Qual período você prefere: **manhã** ou **tarde**?",
                    estado_atual,
                    dados_sessao,
                )

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
            saudacao = "Bom dia" if periodo == "manha" else "Boa tarde"
            resposta = (
                f"{saudacao}! Com qual destas opções teremos o prazer de lhe atender?\n\n"
                f"{_formatar_opcoes_horario(opcoes)}\n\n"
                "Por favor, digite o número da opção que prefere."
            )
            proximo_estado = "aguardando_horario"

        elif estado_atual == "confirmar_sintoma_existente":
            sintoma_anterior = dados_sessao.get("sintoma_anterior", "não informado")
            if _resposta_afirmativa(texto) or sintoma_anterior.lower() in texto.lower():
                dados_sessao["sintoma"] = sintoma_anterior
                resposta = (
                    "Entendi, o sintoma continua o mesmo. Agora me fale se você irá pelo convênio ou prefere atendimento particular."
                )
                proximo_estado = "aguardando_convenio"
            elif _resposta_negativa(texto):
                resposta = (
                    "Certo, então descreva o novo sintoma ou motivo da sua consulta em uma frase, por favor."
                )
                proximo_estado = "confirmar_sintoma_existente"
            elif len(texto) >= 3:
                dados_sessao["sintoma"] = texto
                resposta = (
                    f"Obrigado. Registrei o novo sintoma: '{texto}'. Agora preciso saber se você irá pelo convênio ou prefere atendimento particular."
                )
                proximo_estado = "aguardando_convenio"
            else:
                resposta = (
                    "Desculpe, não entendi. O sintoma continua o mesmo ou há algum sintoma novo?"
                )
                proximo_estado = "confirmar_sintoma_existente"

        elif estado_atual == "aguardando_horario":
            opcoes_horario = dados_sessao.get("opcoes_horario", [])
            if not opcoes_horario:
                return (
                    "Ocorreu um erro ao recuperar as opções de horário. Por favor, digite manhã ou tarde novamente.",
                    "aguardando_preferencia_horario",
                    dados_sessao,
                )

            escolha_extraida = dados_extraidos_llm.get("escolha", "").strip()
            escolha_texto = escolha_extraida if escolha_extraida else texto
            escolha = None
            selected = None
            if escolha_texto.isdigit():
                escolha = int(escolha_texto)
                for opcao in opcoes_horario:
                    if opcao["opcao"] == escolha:
                        selected = opcao
                        break
            else:
                texto_normalizado = _normalizar_texto(escolha_texto)
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
                    "Desculpe, não reconheci essa opção. Escolha um número válido entre os horários apresentados.",
                    estado_atual,
                    dados_sessao,
                )

            if selected.get("db_id") is not None:
                reservado = await _reservar_slot_db(selected["db_id"], dados_sessao.get("nome", "Paciente"))
                if not reservado:
                    periodo = dados_sessao.get("preferencia_horario")
                    if periodo:
                        opcoes = await _obter_horarios_disponiveis(periodo)
                        dados_sessao["opcoes_horario"] = opcoes
                    else:
                        dados_sessao.pop("opcoes_horario", None)
                        return (
                            "O horário escolhido acabou de ser reservado por outra pessoa. Por favor, digite manhã ou tarde novamente.",
                            "aguardando_preferencia_horario",
                            dados_sessao,
                        )

                    if not dados_sessao.get("opcoes_horario"):
                        return (
                            "O horário escolhido acabou de ser reservado por outra pessoa e não conseguimos obter mais horários no momento. Por favor, tente outro período.",
                            "aguardando_preferencia_horario",
                            dados_sessao,
                        )

                    return (
                        f"O horário escolhido acabou de ser reservado por outra pessoa. Aqui estão as novas opções disponíveis:\n\n{_formatar_opcoes_horario(dados_sessao['opcoes_horario'])}",
                        "aguardando_horario",
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
                "Seu agendamento foi confirmado com sucesso!\n\n"
                f"Resumo da sua reserva:\n- Nome: {nome}\n- Convênio: {convenio}\n- Horário: {horario}\n\n"
                "Local: Connect Tower, Av. Paulista, 1234, São Paulo - SP\n\n"
                "Se precisar alterar ou tiver alguma dúvida, estou à disposição."
            )
            proximo_estado = "concluido"

        else:
            dados_sessao.clear()
            resposta = "Seu atendimento já foi concluído. Caso precise de novo agendamento, digite 'olá'."
            proximo_estado = "inicio"

        return resposta, proximo_estado, dados_sessao
    except Exception:
        logger.exception("Erro inesperado no processamento do fluxo de atendimento")
        return (
            "Desculpe, ocorreu um problema interno ao processar sua solicitação. Tente novamente em alguns instantes.",
            estado_atual,
            dados_sessao,
        )
