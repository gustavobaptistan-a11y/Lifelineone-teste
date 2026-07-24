# Visao geral

O Lifeline Bot e um backend FastAPI para atendimento clinico via WhatsApp.

O fluxo atual recebe mensagens em `POST /webhook`, carrega uma sessao por `remoteJid`, executa uma maquina de estados deterministica e salva a sessao no PostgreSQL.

Estado atual conhecido:

- A maquina de estados e funcional em nivel de prototipo.
- A deteccao de urgencia e deterministica.
- A Evolution API possui um cliente implementado, mas ainda nao esta conectada ao fluxo principal.
- A agenda real, Redis e o agente LLM de producao ainda precisam ser integrados.

Fonte complementar: `PROJECT_CONTEXT.md` e o briefing tecnico na raiz do projeto.
