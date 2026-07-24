# Inteligencia artificial

O briefing define um agente conversacional com saida JSON estruturada. O backend atual ainda nao executa um LLM no fluxo principal.

Existe um servico mock em `app/services/llm_service.py` e simuladores OpenAI em `tests/`.

Requisitos para evolucao:

- prompt de sistema versionado;
- extracao estruturada validada;
- limites de contexto e custo;
- fallback para respostas invalidas;
- proibicao de diagnostico;
- estados e urgencia controlados pelo backend.
