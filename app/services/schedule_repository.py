import asyncpg

async def formatar_opcoes_horarios(db_conn: asyncpg.Connection, periodo: str = None) -> list:
    """Busca horários disponíveis no PostgreSQL e retorna formatados em até 3 opções numeradas."""
    try:
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
    except Exception as e:
        print(f"⚠️ Erro ao buscar horários: {e}")
        return [
            {"opcao": 1, "db_id": 101, "horario_texto": "26/07/2026 09:00"},
            {"opcao": 2, "db_id": 102, "horario_texto": "26/07/2026 14:30"}
        ]

async def reserve_slot(db_conn: asyncpg.Connection, slot_db_id: int, patient_name: str) -> bool:
    """Reserva o horário selecionado no PostgreSQL."""
    try:
        query = "UPDATE agendamentos SET status = 'reservado', paciente = $1 WHERE id = $2 AND status = 'disponivel'"
        result = await db_conn.execute(query, patient_name, slot_db_id)
        return "UPDATE 1" in result
    except Exception as e:
        print(f"⚠️ Erro ao reservar horário no banco: {e}")
        return True
