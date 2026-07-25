import asyncio

from app.services import session_repository
from app.config import settings


class FakeRedisClient:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value
        return True


def test_obter_e_salvar_sessao_com_redis_fallback(monkeypatch):
    fake_client = FakeRedisClient()

    async def fake_init_redis_client():
        return fake_client

    monkeypatch.setattr(session_repository, "_init_redis_client", fake_init_redis_client)
    monkeypatch.setattr(settings, "REDIS_ENABLED", True)
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")

    remote_jid = "5561999990003@s.whatsapp.net"
    dados = {"estado": "inicio", "nome": "Teste"}

    asyncio.run(session_repository.salvar_sessao_async(remote_jid, dados))
    resultado = asyncio.run(session_repository.obter_sessao_async(remote_jid))

    assert resultado == dados


def test_obter_sessao_fallback_para_memoria_quando_sem_redis_e_postgres(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_ENABLED", False)
    monkeypatch.setattr(settings, "REDIS_URL", "")
    monkeypatch.setattr(settings, "DATABASE_URL", "")

    remote_jid = "5561999990004@s.whatsapp.net"
    dados = {"estado": "inicio", "nome": "Fallback"}

    asyncio.run(session_repository.salvar_sessao_async(remote_jid, dados))
    resultado = asyncio.run(session_repository.obter_sessao_async(remote_jid))

    assert resultado == dados
