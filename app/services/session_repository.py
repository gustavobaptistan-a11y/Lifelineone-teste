import json
from app.database import obter_conexao, inicializar_banco

# Garante que a tabela existe ao carregar o módulo
inicializar_banco()

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
        print(f"[Sessão] Erro ao obter sessão do Postgres: {e}")
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
        print(f"[Sessão] Erro ao salvar sessão no Postgres: {e}")
