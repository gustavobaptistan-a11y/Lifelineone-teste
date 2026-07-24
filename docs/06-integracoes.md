# Integracoes

## Evolution API

O cliente esta em `app/services/evolution_service.py`. Ele prepara envio de texto por HTTP e usa a chave da API no header `apikey`.

A chamada e feita pelo router depois que a resposta e a sessao sao processadas. O envio e controlado por `EVOLUTION_SEND_ENABLED` e fica desabilitado por padrao para testes locais.

Falhas de envio nao desfazem o processamento da conversa. O resultado e registrado como `envio.status` na resposta e no log da aplicacao.

## PostgreSQL

Usado atualmente para sessoes por meio de `psycopg2`.

## OpenAI

Usada nos simuladores de pacientes. Nao esta conectada ao fluxo principal.

Redis, filas, OAuth e outros gateways nao foram encontrados no repositorio.
