import json
import logging
import asyncio
from typing import Any

from app.config import settings
from app.database import obter_conexao

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis  # type: ignore[import]
except ImportError:  # pragma: no cover
    aioredis = None

_redis_client: Any | None = None
_in_memory_sessions: dict[str, dict] = {}


def _get_redis_key(remote_jid: str) -> str:
    return f"{settings.REDIS_SESSION_PREFIX}{remote_jid}"


async def _init_redis_client() -> Any | None:
    global _redis_client
    if not settings.REDIS_ENABLED or not settings.REDIS_URL:
        return None
    if aioredis is None:
        logger.warning("Redis nao disponivel no ambiente; fallback desabilitado.")
        return None
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def _obter_sessao_redis(remote_jid: str) -> dict | None:
    client = await _init_redis_client()
    if client is None:
        return None
    try:
        dados = await client.get(_get_redis_key(remote_jid))
        if not dados:
            return None
        return json.loads(dados)
    except Exception:
        logger.exception("Erro ao ler sessao do Redis")
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
        logger.exception("Erro ao salvar sessao no Redis")
        return False


def obter_sessao(remote_jid: str) -> dict:
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT dados FROM sessoes WHERE remote_jid = %s;", (remote_jid,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado and "dados" in resultado:
            return resultado["dados"]
        
        sessao_inicial = {"estado": "inicio"}
        salvar_sessao(remote_jid, sessao_inicial)
        return sessao_inicial
    except Exception as e:
        logger.exception("Erro ao obter sessão do Postgres: %s", e)
        return {"estado": "inicio"}


def salvar_sessao(remote_jid: str, dados_sessao: dict):
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessoes (remote_jid, dados, atualizado_em)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (remote_jid) 
            DO UPDATE SET dados = EXCLUDED.dados, atualizado_em = CURRENT_TIMESTAMP;
        """, (remote_jid, json.dumps(dados_sessao)))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.exception("Erro ao salvar sessão no Postgres: %s", e)


async def obter_sessao_async(remote_jid: str) -> dict:
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        sessao = await _obter_sessao_redis(remote_jid)
        if sessao is not None:
            return sessao

    if settings.DATABASE_URL:
        sessao = await asyncio.to_thread(obter_sessao, remote_jid)
        if sessao is not None and settings.REDIS_ENABLED and settings.REDIS_URL:
            await _salvar_sessao_redis(remote_jid, sessao)
        return sessao

    return _in_memory_sessions.get(remote_jid, {"estado": "inicio"})


async def salvar_sessao_async(remote_jid: str, dados_sessao: dict):
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        saved = await _salvar_sessao_redis(remote_jid, dados_sessao)
        if saved:
            if settings.DATABASE_URL:
                await asyncio.to_thread(salvar_sessao, remote_jid, dados_sessao)
            return

    if settings.DATABASE_URL:
        return await asyncio.to_thread(salvar_sessao, remote_jid, dados_sessao)

    _in_memory_sessions[remote_jid] = dados_sessao
