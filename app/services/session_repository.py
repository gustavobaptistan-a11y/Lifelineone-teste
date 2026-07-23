import json
import os

class SessionRepository:
    def __init__(self, arquivo_db="sessions.json"):
        self.arquivo_db = arquivo_db
        self._carregar()

    def _carregar(self):
        if os.path.exists(self.arquivo_db):
            try:
                with open(self.arquivo_db, "r", encoding="utf-8") as f:
                    self.sessoes = json.load(f)
            except Exception:
                self.sessoes = {}
        else:
            self.sessoes = {}

    def _salvar(self):
        try:
            with open(self.arquivo_db, "w", encoding="utf-8") as f:
                json.dump(self.sessoes, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar arquivo de sessões: {e}")

    def obter_sessao(self, remote_jid: str) -> dict:
        self._carregar()
        return self.sessoes.get(remote_jid, {"estado": "inicio", "historico": []})

    def salvar_sessao(self, remote_jid: str, dados_sessao: dict):
        self.sessoes[remote_jid] = dados_sessao
        self._salvar()

# Instância global exportada para consumo nos routers
session_repository = SessionRepository()
