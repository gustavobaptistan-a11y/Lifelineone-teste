# Integracoes

## Evolution API

O cliente esta em `app/services/evolution_service.py`. Ele envia texto por HTTP usando:

- endpoint: `/message/sendText/{EVOLUTION_INSTANCE_NAME}`;
- header: `apikey`;
- payload: `{"number": "<numero_sem_jid>", "text": "<mensagem>"}`.

A chamada e feita pelo router depois que a resposta e a sessao sao processadas. O envio e controlado por `EVOLUTION_SEND_ENABLED` e fica desabilitado por padrao para testes locais. Quando desabilitado, o webhook retorna `envio.status = desabilitado` sem tentar chamada HTTP externa.

Para testar envio real ao WhatsApp, configure no `.env`:

```env
EVOLUTION_SEND_ENABLED=true
EVOLUTION_API_URL=https://api-wpp.ghosthub.com.br
EVOLUTION_API_KEY=<sua_chave>
EVOLUTION_INSTANCE_NAME=<sua_instancia>
```

Falhas de envio nao desfazem o processamento da conversa. O resultado e registrado em `envio.status` na resposta do webhook e no log da aplicacao.

## PostgreSQL

Usado para persistencia de sessoes e agendamentos quando `DATABASE_URL` esta configurado.

## Redis

Suportado como cache primario de sessao quando `REDIS_ENABLED=true`, com fallback para PostgreSQL e memoria local.

## OpenAI

Usada para extracao estruturada quando `OPENAI_API_KEY` esta configurada. Se estiver desabilitada ou falhar, o fluxo continua com validacoes locais.
