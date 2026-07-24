# API

## GET /

Retorna uma mensagem simples indicando que o servidor esta ativo.

## POST /webhook

Recebe evento com dados da mensagem da Evolution API.

Campos atualmente lidos:

- `data.key.remoteJid`;
- `data.key.fromMe`;
- `data.message.conversation`;
- `data.message.extendedTextMessage.text`.

O payload de entrada agora e validado por modelos Pydantic. `remoteJid` e obrigatorio, mensagens com `fromMe=true` sao ignoradas e mensagens sem texto nao avancam para a maquina de estados.

Quando a mensagem e processada, a resposta inclui `envio.status`, que pode ser `desabilitado`, `enviado` ou `erro`.

Idempotencia, autenticacao do webhook e resposta publica estavel ainda sao pontos de evolucao.
