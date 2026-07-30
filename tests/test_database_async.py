import asyncio


def test_init_and_close_db_pool(monkeypatch):
    created = {}

    class DummyPool:
        async def close(self):
            created['closed'] = True

    async def fake_create_pool(dsn, min_size, max_size):
        created['created'] = True
        return DummyPool()

    monkeypatch.setattr('asyncpg.create_pool', fake_create_pool)

    import app.config as config
    # garantir que DATABASE_URL esteja setada para o teste
    monkeypatch.setattr(config.settings, 'DATABASE_URL', 'postgresql://user:pass@localhost/db')

    import app.database_async as db_async

    asyncio.run(db_async.init_db_pool())
    assert created.get('created')
    asyncio.run(db_async.close_db_pool())
    assert created.get('closed')


def test_inicializar_banco_cria_tabela_agendamentos(monkeypatch):
    executed_queries = []
    committed = []
    closed = []

    class DummyCursor:
        def execute(self, query, params=None):
            executed_queries.append(query)

        def close(self):
            pass

    class DummyConnection:
        def __init__(self, cursor):
            self._cursor = cursor

        def cursor(self):
            return self._cursor

        def commit(self):
            committed.append(True)

        def close(self):
            closed.append(True)

    cursor = DummyCursor()
    conn = DummyConnection(cursor)

    def fake_obter_conexao():
        return conn

    import app.database as database
    monkeypatch.setattr(database, 'obter_conexao', fake_obter_conexao)

    database.inicializar_banco()

    assert any(
        "CREATE TABLE IF NOT EXISTS agendamentos" in query
        for query in executed_queries
    )
    assert committed
