import logging

from psycopg2.extras import Json

from app.services.agendamento_repository import agendamento_repository


def test_salvar_agendamento_persiste_no_postgres(monkeypatch):
    executed = {}

    class DummyCursor:
        def execute(self, query, params=None):
            executed["query"] = query
            executed["params"] = params

        def close(self):
            executed["cursor_closed"] = True

    class DummyConnection:
        def __init__(self, cursor):
            self._cursor = cursor
            self.committed = False
            self.closed = False

        def cursor(self):
            return self._cursor

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    cursor = DummyCursor()
    conn = DummyConnection(cursor)

    def fake_obter_conexao():
        return conn

    monkeypatch.setattr("app.services.agendamento_repository.obter_conexao", fake_obter_conexao)

    dados_sessao = {
        "nome": "Teste Paciente",
        "sintoma": "Dor de cabeça",
        "convenio": "Convênio X",
        "primeira_consulta": True,
        "preferencia_horario": "manha",
        "horario": "01/01/2026 09:00",
    }

    agendamento_repository.salvar_agendamento("5561999999999@s.whatsapp.net", dados_sessao)

    assert "INSERT INTO agendamentos_confirmados" in executed["query"]
    assert executed["params"][0] == "5561999999999@s.whatsapp.net"
    assert isinstance(executed["params"][1], Json)
    assert conn.committed is True
    assert executed["cursor_closed"] is True
    assert conn.closed is True


def test_salvar_agendamento_sem_database_url_nao_lanca(monkeypatch, caplog):
    def fake_obter_conexao():
        raise RuntimeError("DATABASE_URL não configurada")

    monkeypatch.setattr("app.services.agendamento_repository.obter_conexao", fake_obter_conexao)

    dados_sessao = {
        "nome": "Teste Paciente",
        "sintoma": "Dor de cabeça",
        "convenio": "Convênio X",
        "primeira_consulta": True,
        "preferencia_horario": "manha",
        "horario": "01/01/2026 09:00",
    }

    with caplog.at_level(logging.WARNING):
        agendamento_repository.salvar_agendamento("5561999999999@s.whatsapp.net", dados_sessao)

    assert "Não há DATABASE_URL configurada" in caplog.text
