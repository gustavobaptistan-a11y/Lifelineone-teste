import json
import logging
from datetime import datetime

from app.config import settings
from app.database_async import get_pool

logger = logging.getLogger(__name__)


async def salvar_agendamento_async(remote_jid: str, dados_sessao: dict):
    """
    Salva o agendamento completo de forma assíncrona no banco de dados.
    """
    pool = get_pool()
    if not pool:
        logger.warning(
            "Pool de conexão não disponível. Agendamento não foi salvo no PostgreSQL."
        )
        return

    registro_completo = {
        "id_agendamento": f"AG-{int(datetime.now().timestamp())}",
        "whatsapp_jid": remote_jid,
        "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_agendamento": "CONFIRMADO",
        "paciente": {
            "nome_completo": dados_sessao.get("nome", "Não informado"),
            "contato": remote_jid.split("@")[0],
        },
        "triagem": {
            "sintoma_principal": dados_sessao.get("sintoma", "Não informado"),
            "modalidade_atendimento": dados_sessao.get("convenio", "Não informado"),
            "tipo_consulta": (
                "Primeira consulta"
                if dados_sessao.get("primeira_consulta") is True
                else "Retorno"
                if dados_sessao.get("primeira_consulta") is False
                else "Não informado"
            ),
        },
        "agendamento": {
            "preferencia_periodo": dados_sessao.get(
                "preferencia_horario", "Não informado"
            ),
            "opcao_horario_escolhida": dados_sessao.get("horario", "Não informado"),
        },
    }

    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO agendamentos_confirmados (remote_jid, dados) VALUES ($1, $2)",
                remote_jid,
                json.dumps(registro_completo),
            )
        logger.info(
            "Agendamento salvo no Postgres: id=%s paciente=%s",
            registro_completo["id_agendamento"],
            registro_completo["paciente"]["nome_completo"],
        )
    except Exception:
        logger.exception("Falha ao persistir agendamento confirmado no PostgreSQL")

# Para manter a compatibilidade com a forma como era importado,
# podemos criar uma instância/variável com o mesmo nome.
agendamento_repository = type("AgendamentoRepository", (), {"salvar_agendamento_async": salvar_agendamento_async})()
