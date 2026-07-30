# Visao geral

O Lifeline Bot e um backend FastAPI para atendimento clinico via WhatsApp.

O fluxo atual recebe mensagens em `POST /webhook`, carrega uma sessao por `remoteJid` e `conversation_id`, executa uma maquina de estados deterministica, salva a sessao e tenta enviar a resposta pela Evolution API conforme configuracao.

Estado atual conhecido:

- A maquina de estados e funcional em nivel de backend/prototipo.
- A deteccao de urgencia e deterministica e acontece antes do LLM.
- A Evolution API possui cliente implementado e e chamada pelo webhook; falta validar envio real em WhatsApp.
- Redis ja e suportado como persistencia/cache de sessao quando habilitado, com fallback para PostgreSQL e memoria local.
- O LLM ja possui extracao JSON estruturada via OpenAI SDK; o briefing cita LangChain, entao essa decisao ainda precisa ser alinhada.
- Google Calendar possui adaptador e pode ser chamado no fluxo, mas nao substitui a reserva no banco como fonte de verdade.
- Deploy publico, teste real via WhatsApp e demonstracao final continuam pendentes.

Fonte complementar: `PROJECT_CONTEXT.md`, `docs/BRIEFING_Rauder_de_Azevedo_CTO.md` e `docs/18-status-briefing.md`.