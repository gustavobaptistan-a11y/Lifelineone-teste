# Changelog

## [Unreleased]

### Adicionado
- Suporte a persistência de sessão via Redis com fallback para PostgreSQL e memória local.
- Variáveis de ambiente Redis adicionadas: `REDIS_ENABLED`, `REDIS_URL`, `REDIS_SESSION_PREFIX` e `REDIS_SESSION_TTL_SECONDS`.
- Documentação atualizada para refletir a integração Redis e o comportamento de fallback.
- Novo teste de sessão em `tests/test_session_repository.py` cobrindo Redis e fallback em memória.

### Corrigido
- Comportamento do serviço Evolution para retornar `envio.status = desabilitado` quando `EVOLUTION_SEND_ENABLED=false`.

### Validado
- Suíte completa de testes executada com sucesso: `24 passed`.
