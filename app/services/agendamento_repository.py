import json
import os
import logging
from datetime import datetime
import asyncio

from psycopg2.extras import Json

from app.database import obter_conexao

logger = logging.getLogger(__name__)


class AgendamentoRepository:
    def __init__(self, arquivo_db="agendamentos_db.json"):
        self.arquivo_db = arquivo_db
        self._inicializar()

    def _inicializar(self):
        if not os.path.exists(self.arquivo_db):
            with open(self.arquivo_db, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    def salvar_agendamento(self, remote_jid: str, dados_sessao: dict):
        """
        Salva o agendamento completo estruturado com todas as variáveis do fluxo.
        """
        # Mapeamento completo e padronizado do registro clínico
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


    async def salvar_agendamento_async(self, remote_jid: str, dados_sessao: dict):
        return await asyncio.to_thread(self.salvar_agendamento, remote_jid, dados_sessao)


agendamento_repository = AgendamentoRepository()
