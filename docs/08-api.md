# API

## GET /

Retorna uma mensagem simples indicando que o servidor esta ativo.

## POST /webhook

Recebe eventos do EvolutionGO no formato de webhook e processa a conversa do paciente.

### Payload esperado

O endpoint consome payloads no formato abaixo:

- `data.key.remoteJid`
- `data.key.fromMe`
- `data.message.conversation`
- `data.message.extendedTextMessage.text`

### Regras de processamento

- Mensagens com `fromMe=true` sao ignoradas.
- Mensagens sem texto retornam `status: ignorado`.
- O estado da conversa e carregado da sessao existente via `remoteJid`.
- A sessao e atualizada e salva preferencialmente no Redis via `app/services/session_repository.py`; se Redis estiver desabilitado ou indisponível, o PostgreSQL é usado como fallback.
- Se o fluxo chegar em `concluido`, o agendamento e salvo no banco.
- O sistema tenta enviar resposta usando EvolutionGO.

### Autenticacao do webhook

Se `WEBHOOK_SECRET` estiver configurado, o webhook exige um dos seguintes headers:

- `X-Webhook-Secret: <segredo>`
- `Authorization: Bearer <segredo>`

A validacao e feita apenas quando `WEBHOOK_SECRET` esta definido.

### Resposta de API

O endpoint responde sempre com JSON contendo pelo menos:

- `status`
- `estado_anterior`
- `estado_final`
- `proximo_estado`
- `resposta`
- `resposta_enviada`
- `envio`

Onde `envio.status` pode ser:

- `desabilitado` (quando `EVOLUTION_SEND_ENABLED=false`)
- `enviado` (quando a chamada EvolutionGO ocorreu)
- `erro` (quando houve falha na chamada EvolutionGO)

### Observacoes

- A autenticacao e a idempotencia do webhook ainda podem ser melhoradas em iteracoes futuras.
- O fluxo de conversa e controlado pelo backend; o LLM apenas extrai e valida dados.
