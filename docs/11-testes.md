# Testes

A pasta `tests/` contem scripts de simulacao HTTP, verificacao de seguranca, testes de Evolution, simuladores OpenAI e verificacao de banco.

Os testes atuais nao formam uma suite unitaria coesa. Parte deles espera campos e estados diferentes do contrato atual.

A estrategia alvo deve incluir:

- testes unitarios da urgencia e da maquina de estados;
- testes de contrato do webhook;
- mocks para Evolution, LLM, Redis e PostgreSQL;
- testes de concorrencia da reserva;
- testes de mensagens duplicadas e fora de ordem;
- teste ponta a ponta controlado.
