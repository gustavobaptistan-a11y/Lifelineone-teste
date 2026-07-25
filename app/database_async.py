import logging
from typing import Optional
import asyncpg
from app.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.pool.Pool] = None


async def init_db_pool():
    global _pool
    if _pool is not None:
        logger.debug("DB pool already initialized")
        return _pool

    database_url = settings.DATABASE_URL
    if not database_url:
        logger.warning("DATABASE_URL não configurada; pulando criação de pool")
        return None

    try:
        _pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)
        logger.info("Asyncpg pool criado com sucesso")
        return _pool
    except Exception as e:
        logger.exception("Erro ao criar asyncpg pool: %s", e)
        raise


def get_pool() -> Optional[asyncpg.pool.Pool]:
    return _pool


async def close_db_pool():
    global _pool
    if _pool is None:
        return
    try:
        await _pool.close()
        logger.info("Asyncpg pool fechado")
    except Exception:
        logger.exception("Erro ao fechar asyncpg pool")
    finally:
        _pool = None
