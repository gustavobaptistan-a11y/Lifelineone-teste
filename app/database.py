import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

def obter_conexao():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurada")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

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
        conn.commit()
        cursor.close()
        conn.close()
        print("[Banco de Dados] Tabela 'sessoes' verificada/criada com sucesso no PostgreSQL.")
    except Exception as e:
        print(f"[Banco de Dados] Erro ao conectar ou inicializar o PostgreSQL: {e}")

# Função assíncrona para compatibilidade com o await do main.py
async def connect_to_db():
    inicializar_banco()

async def close_db_connection():
    pass
