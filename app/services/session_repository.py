import json
import logging
import asyncio
from app.database import obter_conexao

logger = logging.getLogger(__name__)


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
        
        # Se não existir, cria padrão
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
    return await asyncio.to_thread(obter_sessao, remote_jid)


async def salvar_sessao_async(remote_jid: str, dados_sessao: dict):
    return await asyncio.to_thread(salvar_sessao, remote_jid, dados_sessao)
