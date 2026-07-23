import asyncpg
from app.config import settings

pool = None

async def connect_to_db():
    global pool
    if hasattr(settings, "DATABASE_URL") and settings.DATABASE_URL:
        try:
            pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
            print("✅ Conexão com o banco de dados PostgreSQL estabelecida!")
        except Exception as e:
            print(f"⚠️ Erro ao conectar ao banco de dados: {e}")

async def close_db_connection():
    global pool
    if pool:
        await pool.close()
        print("🔒 Conexão com o banco de dados encerrada!")

async def get_db_connection():
    global pool
    if pool:
        async with pool.acquire() as connection:
            yield connection
    else:
        yield None
