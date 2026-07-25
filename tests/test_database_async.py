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
