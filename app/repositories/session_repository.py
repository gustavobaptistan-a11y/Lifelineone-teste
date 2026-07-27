import json
import logging
from typing import Any

import asyncpg

from app.config import settings
from app.database_async import get_pool

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

_redis_client: Any | None = None
_in_memory_sessions: dict[str, dict] = {}


def _get_redis_key(remote_jid: str) -> str:
    return f"{settings.REDIS_SESSION_PREFIX}{remote_jid}"


async def _init_redis_client() -> Any | None:
    global _redis_client
    if not settings.REDIS_ENABLED or not settings.REDIS_URL or aioredis is None:
        return None
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            logger.exception("Não foi possível conectar ao Redis.")
            return None
    return _redis_client


async def _obter_sessao_redis(remote_jid: str) -> dict | None:
    client = await _init_redis_client()
    if client is None:
        return None
    try:
        dados = await client.get(_get_redis_key(remote_jid))
        return json.loads(dados) if dados else None
    except Exception:
        logger.exception("Erro ao ler sessão do Redis")
        return None


async def _salvar_sessao_redis(remote_jid: str, dados_sessao: dict) -> bool:
    client = await _init_redis_client()
    if client is None:
        return False
    try:
        await client.set(
            _get_redis_key(remote_jid),
            json.dumps(dados_sessao),
            ex=settings.REDIS_SESSION_TTL_SECONDS,
        )
        return True
    except Exception:
        logger.exception("Erro ao salvar sessão no Redis")
        return False


async def _obter_sessao_db_async(remote_jid: str) -> dict | None:
    pool = get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            resultado = await conn.fetchrow(
                "SELECT dados FROM sessoes WHERE remote_jid = $1;", remote_jid
            )
            if resultado and "dados" in resultado:
                return json.loads(resultado["dados"])

        # Se não houver sessão, cria uma inicial
        sessao_inicial = {"estado": "inicio"}
        await _salvar_sessao_db_async(remote_jid, sessao_inicial)
        return sessao_inicial
    except Exception:
        logger.exception("Erro ao obter sessão do Postgres de forma assíncrona")
        return None


async def _salvar_sessao_db_async(remote_jid: str, dados_sessao: dict):
    pool = get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sessoes (remote_jid, dados, atualizado_em)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (remote_jid)
                DO UPDATE SET dados = EXCLUDED.dados, atualizado_em = CURRENT_TIMESTAMP;
            """,
                remote_jid,
                json.dumps(dados_sessao),
            )
    except Exception:
        logger.exception("Erro ao salvar sessão no Postgres de forma assíncrona")


async def obter_sessao_async(remote_jid: str) -> dict:
    """Tenta obter a sessão do Redis, depois do DB, e por último da memória."""
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        sessao = await _obter_sessao_redis(remote_jid)
        if sessao is not None:
            return sessao

    if settings.DATABASE_URL:
        sessao = await _obter_sessao_db_async(remote_jid)
        if sessao is not None:
            if settings.REDIS_ENABLED and settings.REDIS_URL:
                await _salvar_sessao_redis(remote_jid, sessao)  # Cache miss, so we save it
            return sessao

    # Fallback final para memória
    return _in_memory_sessions.get(remote_jid, {"estado": "inicio"})


async def salvar_sessao_async(remote_jid: str, dados_sessao: dict):
    """Salva a sessão no Redis (se ativo) e no banco de dados, com fallback para memória."""
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        await _salvar_sessao_redis(remote_jid, dados_sessao)

    if settings.DATABASE_URL:
        await _salvar_sessao_db_async(remote_jid, dados_sessao)
        return

    # Fallback final para memória
    _in_memory_sessions[remote_jid] = dados_sessao

