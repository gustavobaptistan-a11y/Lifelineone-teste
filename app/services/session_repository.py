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


def _make_session_key(remote_jid: str, conversation_id: str | None = None) -> str:
    if conversation_id:
        return f"{remote_jid}|{conversation_id}"
    return remote_jid


def _get_redis_key(remote_jid: str, conversation_id: str | None = None) -> str:
    return f"{settings.REDIS_SESSION_PREFIX}{_make_session_key(remote_jid, conversation_id)}"


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


async def _obter_sessao_redis(remote_jid: str, conversation_id: str | None = None) -> dict | None:
    client = await _init_redis_client()
    if client is None:
        return None
    try:
        dados = await client.get(_get_redis_key(remote_jid, conversation_id))
        if not dados:
            return None
        return json.loads(dados)
    except Exception:
        logger.exception("Erro ao ler sessao do Redis")
        return None


async def _salvar_sessao_redis(remote_jid: str, dados_sessao: dict, conversation_id: str | None = None) -> bool:
    client = await _init_redis_client()
    if client is None:
        return False
    try:
        await client.set(
            _get_redis_key(remote_jid, conversation_id),
            json.dumps(dados_sessao),
            ex=settings.REDIS_SESSION_TTL_SECONDS,
        )
        return True
    except Exception:
        logger.exception("Erro ao salvar sessao no Redis")
        return False


def obter_sessao(remote_jid: str, conversation_id: str | None = None) -> dict:
    session_key = _make_session_key(remote_jid, conversation_id)
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT dados FROM sessoes WHERE remote_jid = %s;", (session_key,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado and "dados" in resultado:
            return resultado["dados"]
        
        sessao_inicial = {"estado": "inicio"}
        salvar_sessao(remote_jid, sessao_inicial, conversation_id)
        return sessao_inicial
    except Exception as e:
        logger.exception("Erro ao obter sessão do Postgres: %s", e)
        return {"estado": "inicio"}


def salvar_sessao(remote_jid: str, dados_sessao: dict, conversation_id: str | None = None):
    session_key = _make_session_key(remote_jid, conversation_id)
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessoes (remote_jid, dados, atualizado_em)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (remote_jid) 
            DO UPDATE SET dados = EXCLUDED.dados, atualizado_em = CURRENT_TIMESTAMP;
        """, (session_key, json.dumps(dados_sessao)))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.exception("Erro ao salvar sessão no Postgres: %s", e)


async def obter_sessao_async(remote_jid: str, conversation_id: str | None = None) -> dict:
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        sessao = await _obter_sessao_redis(remote_jid, conversation_id)
        if sessao is not None:
            return sessao

    if settings.DATABASE_URL:
        sessao = await asyncio.to_thread(obter_sessao, remote_jid, conversation_id)
        if sessao is not None and settings.REDIS_ENABLED and settings.REDIS_URL:
            await _salvar_sessao_redis(remote_jid, sessao, conversation_id)
        return sessao

    return _in_memory_sessions.get(_make_session_key(remote_jid, conversation_id), {"estado": "inicio"})


def _obter_todas_sessoes_postgres() -> list[dict]:
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT remote_jid, dados, atualizado_em FROM sessoes ORDER BY atualizado_em DESC;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "remote_jid": row["remote_jid"],
                "dados": row["dados"],
                "atualizado_em": row["atualizado_em"],
            }
            for row in rows
        ]
    except Exception:
        logger.exception("Erro ao buscar todas as sessões do Postgres")
        return []


def _delete_sessao_postgres(remote_jid: str, conversation_id: str | None = None):
    conn = obter_conexao()
    cursor = conn.cursor()
    if conversation_id:
        cursor.execute(
            "DELETE FROM sessoes WHERE remote_jid = %s;",
            (_make_session_key(remote_jid, conversation_id),),
        )
    else:
        cursor.execute(
            "DELETE FROM sessoes WHERE remote_jid = %s OR remote_jid LIKE %s;",
            (remote_jid, remote_jid + "|%"),
        )
    conn.commit()
    cursor.close()
    conn.close()


async def _delete_sessao_redis(remote_jid: str, conversation_id: str | None = None):
    client = await _init_redis_client()
    if client is None:
        return
    try:
        if conversation_id:
            await client.delete(_get_redis_key(remote_jid, conversation_id))
        else:
            keys = await client.keys(f"{settings.REDIS_SESSION_PREFIX}{remote_jid}*")
            if keys:
                await client.delete(*keys)
    except Exception:
        logger.exception("Erro ao deletar sessão do Redis")


async def obter_todas_sessoes_async() -> list[dict]:
    sessions: list[dict] = []
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        client = await _init_redis_client()
        if client is not None:
            try:
                keys = await client.keys(f"{settings.REDIS_SESSION_PREFIX}*")
                for key in keys:
                    raw = await client.get(key)
                    if not raw:
                        continue
                    remote_jid = key[len(settings.REDIS_SESSION_PREFIX) :]
                    sessions.append(
                        {
                            "remote_jid": remote_jid,
                            "dados": json.loads(raw),
                            "atualizado_em": None,
                        }
                    )
                return sessions
            except Exception:
                logger.exception("Erro ao buscar sessões no Redis")

    if settings.DATABASE_URL:
        sessions = await asyncio.to_thread(_obter_todas_sessoes_postgres)
        return sessions

    return [
        {"remote_jid": remote_jid, "dados": dados, "atualizado_em": None}
        for remote_jid, dados in _in_memory_sessions.items()
    ]


async def resetar_sessao_async(remote_jid: str, conversation_id: str | None = None):
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        await _delete_sessao_redis(remote_jid, conversation_id)

    if settings.DATABASE_URL:
        await asyncio.to_thread(_delete_sessao_postgres, remote_jid, conversation_id)
        return

    if conversation_id:
        _in_memory_sessions.pop(_make_session_key(remote_jid, conversation_id), None)
    else:
        for key in list(_in_memory_sessions.keys()):
            if key == remote_jid or key.startswith(remote_jid + "|"):
                _in_memory_sessions.pop(key, None)


async def salvar_sessao_async(remote_jid: str, dados_sessao: dict, conversation_id: str | None = None):
    if settings.REDIS_ENABLED and settings.REDIS_URL:
        saved = await _salvar_sessao_redis(remote_jid, dados_sessao, conversation_id)
        if saved:
            if settings.DATABASE_URL:
                await asyncio.to_thread(salvar_sessao, remote_jid, dados_sessao, conversation_id)
            return

    if settings.DATABASE_URL:
        return await asyncio.to_thread(salvar_sessao, remote_jid, dados_sessao, conversation_id)

    _in_memory_sessions[_make_session_key(remote_jid, conversation_id)] = dados_sessao
