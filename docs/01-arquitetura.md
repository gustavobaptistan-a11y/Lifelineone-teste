# Arquitetura

A aplicacao atual e um monolito Python baseado em FastAPI.

Camadas observadas:

- Entrada HTTP: `app/routers/webhook.py`.
- Dominio do fluxo: `app/services/validador_fluxo.py`.
- Sessao: `app/services/session_repository.py`.
- Banco: `app/database.py`.
- Integracoes preparadas: `app/services/evolution_service.py`.
- Componentes experimentais: servico LLM e repositorios de agenda.

A arquitetura alvo deve separar dominio, aplicacao, infraestrutura e interfaces sem quebrar o contrato do webhook. Nenhuma migracao estrutural foi feita nesta etapa.
