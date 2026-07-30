# Inteligencia artificial

O briefing define um agente conversacional com saida JSON estruturada. No projeto atual, o backend usa uma maquina de estados deterministica como fonte da verdade e usa o LLM apenas para extrair dados estruturados da mensagem do paciente.

Implementado atualmente:

- `app/services/llm_service.py` inicializa cliente OpenAI quando `OPENAI_API_KEY` existe.
- `extract_structured()` solicita JSON com `dados_extraidos` e `urgente`.
- Se a API falha ou retorna formato invalido, o fluxo usa fallback local e nao deve travar o atendimento.
- A urgencia critica tambem e detectada de forma deterministica em `app/services/validador_fluxo.py` antes da chamada ao LLM.

Pendencias para atender o briefing com mais rigor:

- Decidir se o requisito de LangChain sera implementado literalmente ou se o OpenAI SDK sera mantido como decisao tecnica documentada.
- Versionar o prompt de sistema em arquivo proprio ou configuracao.
- Validar o JSON retornado com schema Pydantic antes de usar os campos.
- Adicionar testes para timeout, JSON invalido, campos inesperados e indisponibilidade da API.
- Garantir no prompt e no fluxo que o agente nunca forneca diagnostico medico.