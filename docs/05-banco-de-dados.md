# Banco de dados

O fluxo atual usa PostgreSQL para persistir sessoes na tabela `sessoes`.

Campos conhecidos:

- `remote_jid`: chave primaria do contato.
- `dados`: JSONB com estado e dados coletados.
- `atualizado_em`: timestamp da ultima atualizacao.

Existem implementacoes paralelas em JSON e um SQLite local ignorado pelo Git. A agenda PostgreSQL ainda precisa de schema, migracoes, indices, transacoes e reserva concorrente definidos.
