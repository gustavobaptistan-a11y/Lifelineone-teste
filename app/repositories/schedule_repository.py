import logging

import asyncpg

logger = logging.getLogger(__name__)

async def formatar_opcoes_horarios(db_conn: asyncpg.Connection, periodo: str | None = None) -> list:
    """Busca horários disponíveis no PostgreSQL e retorna formatados em até 3 opções numeradas."""
    try:
        if periodo == "manha":
            query = "SELECT id, TO_CHAR(horario, 'DD/MM/YYYY HH24:MI') as data_hora FROM agendamentos WHERE status = 'disponivel' AND EXTRACT(HOUR FROM horario) < 12 LIMIT 3"
        elif periodo == "tarde":
            query = "SELECT id, TO_CHAR(horario, 'DD/MM/YYYY HH24:MI') as data_hora FROM agendamentos WHERE status = 'disponivel' AND EXTRACT(HOUR FROM horario) >= 12 LIMIT 3"
        else:
            query = "SELECT id, TO_CHAR(horario, 'DD/MM/YYYY HH24:MI') as data_hora FROM agendamentos WHERE status = 'disponivel' LIMIT 3"

        rows = await db_conn.fetch(query)
        
        opcoes = []
        for index, row in enumerate(rows, 1):
            opcoes.append({
                "opcao": index,
                "db_id": row["id"],
                "horario_texto": row["data_hora"]
            })
        return opcoes
    except Exception as exc:
        logger.warning("Erro ao buscar horários no banco de dados: %s", exc)
        return []

async def reserve_slot(db_conn: asyncpg.Connection, slot_db_id: int, patient_name: str) -> bool:
    """Reserva o horário selecionado no PostgreSQL."""
    try:
        query = "UPDATE agendamentos SET status = 'reservado', paciente = $1 WHERE id = $2 AND status = 'disponivel'"
        result = await db_conn.execute(query, patient_name, slot_db_id)
        return "UPDATE 1" in result
    except Exception as exc:
        logger.warning("Erro ao reservar horário no banco de dados: %s", exc)
        return False
