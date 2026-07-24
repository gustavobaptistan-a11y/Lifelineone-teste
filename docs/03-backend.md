# Backend

Ponto de entrada: `main.py`.

Rotas atuais:

- `GET /`: resposta simples de disponibilidade.
- `POST /webhook`: processamento de mensagens.

O backend utiliza funcoes sincronas de `psycopg2` dentro de uma aplicacao FastAPI assincrona. A inicializacao do schema ocorre no evento de startup; os modulos de repositorio nao devem conectar ao banco durante importacao. Pool de conexoes, autenticacao do webhook, idempotencia e tratamento especifico de erros ainda sao pontos de evolucao.
