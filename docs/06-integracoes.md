# Integracoes

## Evolution API

O cliente esta em `app/services/evolution_service.py`. Ele prepara envio de texto por HTTP e usa a chave da API no header `apikey`.

A chamada e feita pelo router depois que a resposta e a sessao sao processadas. O envio e controlado por `EVOLUTION_SEND_ENABLED` e esta desabilitado por padrao para testes locais; quando desabilitado, o webhook retorna `envio.status = desabilitado` sem tentar a chamada HTTP externa.

Para testar o envio real ao WhatsApp, configure `EVOLUTION_SEND_ENABLED=true` no `.env` e garanta que `EVOLUTION_API_KEY` e `EVOLUTION_INSTANCE_NAME` estejam definidos. Em seguida, execute o servidor local e poste um webhook para `/webhook`; o resultado da entrega aparece em `envio.status`.

Falhas de envio nao desfazem o processamento da conversa. O resultado e registrado como `envio.status` na resposta e no log da aplicacao.

## PostgreSQL

Usado atualmente para sessoes por meio de `psycopg2`.

## OpenAI

Usada nos simuladores de pacientes. Nao esta conectada ao fluxo principal.

O backend agora suporta persistência de sessão via Redis quando `REDIS_ENABLED=true`. Em produção, Redis é usado como cache primário de sessão com fallback para PostgreSQL e depois para memória local se ambos estiverem indisponíveis.
