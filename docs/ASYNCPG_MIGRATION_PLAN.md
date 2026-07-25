# Plano de Migração para asyncpg (pool)

Objetivo
- Migrar chamadas de banco para `asyncpg` com um pool compartilhado, removendo pontos de bloqueio e melhorando concorrência.

Resumo da estratégia (passos pequenos e testáveis)

1. Preparação (1 commit)
   - Adicionar dependência `asyncpg` (já presente).
   - Documentar objetivo e criar um novo módulo `app/database_async.py` (esqueleto) que expõe uma função `get_pool()` e `init_db_pool()`.

2. Inicializar pool (1 commit)
   - Implementar `app/database_async.py` com `asyncpg.create_pool` e variáveis de configuração (`DATABASE_URL`).
   - Garantir que `main.py` inicialize o pool em startup e feche em shutdown.
   - Escrever testes unitários básicos que validem a criação/fechamento do pool (mock).

3. Adaptar repositórios críticos (2-3 commits incrementais)
   - Atualizar `app/services/schedule_repository.py` para usar o pool (async) — testar e validar.
   - Atualizar `app/services/session_repository.py` para usar pool (remover wrappers sync onde possível).
   - Atualizar `app/services/agendamento_repository.py` se usar Postgres (no presente usa JSON local, possivelmente não aplicável).
   - Para cada repositório: implementar mudança, rodar testes, abrir PR.

4. Substituir helpers de conexão (1 commit)
   - Atualizar `app/database.py` (ou manter ambos `database.py` e `database_async.py`) para evitar inconsistências.
   - Atualizar importadores para usar o novo pool (ou oferecer adaptador compatível).

5. Testes de integração e performance (1-2 commits)
   - Rodar testes de integração com uma instância Postgres (docker-compose) e validar concorrência (ex.: simular N requisições simultâneas).
   - Medir latência/throughput antes/depois.

6. Rollout e monitoramento
   - Lançar em staging com métricas ativas (latência DB, erros, CPU). Reverter se aumentar erros.

Riscos e mitigação
- Mudanças quebram contratos SQL: mitigar com testes e PRs pequenos.
- Dependências externas (drivers): garantir versão compatível de `asyncpg` e rodar em CI matrix.
- Mistura de sync/async: manter adaptadores `to_thread` durante transição; evitar fazer grandes mudanças em um único commit.

Estimativa (pessoa experiente)
- Preparação + pool básico: 2-4 horas
- Migrar 1-2 repositórios críticos: 4-8 horas
- Testes de integração/ajustes: 2-4 horas
- Total provável: 8-16 horas (dividido em 4-6 commits pequenos)

Checklist antes de merge
- [ ] Tests unitários atualizados e passando
- [ ] Testes de integração com Postgres passando
- [ ] CI atualizado para rodar integração (opcional)
- [ ] Documentação atualizada (`docs/ASYNCPG_MIGRATION_PLAN.md`)

Observações
- Recomendo manter os wrappers `asyncio.to_thread` apenas enquanto coexistirem chamadas sync; remover gradualmente.
- Priorizar `session_repository` e `schedule_repository` para máxima vantagem de concorrência.
