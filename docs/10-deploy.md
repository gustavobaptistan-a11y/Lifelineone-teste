# Deploy

Este repositorio nao inclui infraestrutura versionada de deploy (Docker, CI/CD ou provedor), pois a camada de infraestrutura e administrada externamente.

## Comando de inicializacao

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Variaveis de ambiente obrigatorias

- `OPENAI_API_KEY`
- `EVOLUTION_API_URL`
- `DATABASE_URL`
- `WEBHOOK_GLOBAL_ENABLED=true`
- `WEBHOOK_GLOBAL_URL`
- `WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=false`

## Variaveis de ambiente opcionais / de comportamento

- `EVOLUTION_API_KEY` (necessario se `EVOLUTION_SEND_ENABLED=true`)
- `EVOLUTION_INSTANCE_NAME` (necessario se `EVOLUTION_SEND_ENABLED=true`)
- `EVOLUTION_SEND_ENABLED` (opcional, false por padrao para testes locais; ative em producao apenas quando quiser envio externo de mensagens)
- `WEBHOOK_SECRET` (opcional, recomendado)

## URL publica do webhook

A aplicacao expoe o endpoint:

- `POST /webhook`

O EvolutionGO deve enviar eventos para a URL publica configurada em `WEBHOOK_GLOBAL_URL` com a rota `/webhook`.

## Health check

Ainda nao ha endpoint de health check versionado. Recomenda-se adicionar um endpoint simples de disponibilidade no futuro.

## Estrategia de logs

Logs sao gerados pelo logger Python e devem ser coletados pela infraestrutura de deploy.

## Rollback

Rollback e feito repondo a versao anterior do app no ambiente de deploy externo.

## Verificacao pos-deploy

- Confirmar que o webhook responde `200` para payloads `messages.upsert`
- Confirmar que `envio.status` aparece em respostas do webhook
- Confirmar persistencia de agendamento no PostgreSQL
- Confirmar que `EVOLUTION_SEND_ENABLED=true` esta ativo em producao somente quando desejado
