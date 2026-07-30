import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings

logger = logging.getLogger(__name__)


def obter_conexao():
    database_url = settings.DATABASE_URL
    if not database_url:
        raise RuntimeError("DATABASE_URL não configurada")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


def inicializar_banco():
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes (
                remote_jid VARCHAR(255) PRIMARY KEY,
                dados JSONB NOT NULL,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agendamentos_confirmados (
                id SERIAL PRIMARY KEY,
                remote_jid VARCHAR(255) NOT NULL,
                dados JSONB NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agendamentos (
                id SERIAL PRIMARY KEY,
                horario TIMESTAMP NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'disponivel',
                paciente TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Tabela 'sessoes' verificada/criada com sucesso no PostgreSQL.")
    except Exception as e:
        logger.exception("Erro ao conectar ou inicializar o PostgreSQL: %s", e)


# Função assíncrona para compatibilidade com o await do main.py
async def connect_to_db():
    inicializar_banco()


async def close_db_connection():
    pass
