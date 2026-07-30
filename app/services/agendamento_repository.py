import json
import os
import logging
from datetime import datetime, timedelta
import asyncio

from psycopg2.extras import Json

from app.database import obter_conexao
from app.database_async import get_pool
from app.services.google_calendar_service import calendar_service

logger = logging.getLogger(__name__)


class AgendamentoRepository:
    def __init__(self, arquivo_db="agendamentos_db.json"):
        self.arquivo_db = arquivo_db
        self._inicializar()

    def _inicializar(self):
        if not os.path.exists(self.arquivo_db):
            with open(self.arquivo_db, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    def _criar_evento_google_calendar(self, registro_completo: dict, dados_sessao: dict):
        """
        Função auxiliar para traduzir os dados da sessão em um evento do Google Calendar.
        """
        if not calendar_service.enabled:
            return

        try:
            inicio = None
            fim = None
            inicio_iso = dados_sessao.get("horario_inicio_iso")
            fim_iso = dados_sessao.get("horario_fim_iso")

            if inicio_iso and fim_iso:
                try:
                    inicio = datetime.fromisoformat(inicio_iso)
                    fim = datetime.fromisoformat(fim_iso)
                except ValueError:
                    inicio = None
                    fim = None

            if inicio is None:
                horario_str = dados_sessao.get("horario")
                if not horario_str:
                    logger.warning("Horário da consulta não encontrado para criar o evento no Google Calendar.")
                    return

                if isinstance(horario_str, str):
                    try:
                        inicio = datetime.strptime(horario_str, "%d/%m/%Y %H:%M")
                    except ValueError:
                        try:
                            inicio = datetime.strptime(horario_str, "%Y-%m-%d %H:%M")
                        except ValueError:
                            inicio = datetime.fromisoformat(horario_str)
                else:
                    inicio = horario_str

                fim = inicio + timedelta(hours=1)

            if fim is None:
                fim = inicio + timedelta(hours=1)

            nome_paciente = registro_completo["paciente"]["nome_completo"]
            sintoma = registro_completo["triagem"]["sintoma_principal"]
            tipo = registro_completo["triagem"]["tipo_consulta"]
            
            titulo = f"Consulta: {nome_paciente} ({tipo})"
            descricao = (
                f"Paciente: {nome_paciente}\n"
                f"Contato: {registro_completo['paciente']['contato']}\n"
                f"Sintoma / Motivo: {sintoma}\n"
                f"Tipo: {tipo}"
            )

            # Chama o serviço do Google Calendar para criar o evento
            evento_criado = calendar_service.criar_evento(
                titulo=titulo,
                inicio=inicio,
                fim=fim,
                descricao=descricao
            )
            logger.info("Evento criado no Google Calendar com sucesso: %s", evento_criado.get("htmlLink"))

        except Exception as e:
            logger.exception("Erro ao criar evento automático no Google Calendar: %s", e)

    def salvar_agendamento(self, remote_jid: str, dados_sessao: dict):
        """
        Salva o agendamento completo estruturado com todas as variáveis do fluxo.
        """
        registro_completo = {
            "id_agendamento": f"AG-{int(datetime.now().timestamp())}",
            "whatsapp_jid": remote_jid,
            "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status_agendamento": "CONFIRMADO",
            "paciente": {
                "nome_completo": dados_sessao.get("nome", "Não informado"),
                "contato": remote_jid.split("@")[0]
            },
            "triagem": {
                "sintoma_principal": dados_sessao.get("sintoma", "Não informado"),
                "modalidade_atendimento": dados_sessao.get("convenio", "Não informado"),
                "tipo_consulta": (
                    "Primeira consulta" if dados_sessao.get("primeira_consulta") is True else
                    "Retorno" if dados_sessao.get("primeira_consulta") is False else
                    "Não informado"
                )
            },
            "agendamento": {
                "preferencia_periodo": dados_sessao.get("preferencia_horario", "Não informado"),
                "opcao_horario_escolhida": dados_sessao.get("horario", "Não informado")
            }
        }

        try:
            conn = obter_conexao()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO agendamentos_confirmados (remote_jid, dados) VALUES (%s, %s)",
                (remote_jid, Json(registro_completo)),
            )
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(
                "Agendamento salvo no Postgres: id=%s paciente=%s",
                registro_completo["id_agendamento"],
                registro_completo["paciente"]["nome_completo"],
            )
        except RuntimeError as exc:
            logger.warning(
                "Não há DATABASE_URL configurada. Agendamento confirmado não foi salvo no PostgreSQL: %s",
                exc,
            )
        except Exception:
            logger.exception("Falha ao persistir agendamento confirmado no PostgreSQL")

        # Integrando a criação do evento no Google Calendar após salvar no banco
        self._criar_evento_google_calendar(registro_completo, dados_sessao)

    async def buscar_ultimo_agendamento_confirmado_async(self, remote_jid: str) -> dict | None:
        pool = get_pool()
        if not pool:
            return None

        try:
            async with pool.acquire() as conn:
                resultado = await conn.fetchrow(
                    "SELECT dados FROM agendamentos_confirmados WHERE remote_jid = $1 ORDER BY criado_em DESC LIMIT 1",
                    remote_jid,
                )
                if resultado and resultado.get("dados"):
                    return json.loads(resultado["dados"])
        except Exception:
            logger.exception(
                "Falha ao buscar o último agendamento confirmado para %s",
                remote_jid,
            )
        return None

    async def salvar_agendamento_async(self, remote_jid: str, dados_sessao: dict):
        return await asyncio.to_thread(self.salvar_agendamento, remote_jid, dados_sessao)


agendamento_repository = AgendamentoRepository()