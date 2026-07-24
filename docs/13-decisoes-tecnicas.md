# Decisoes tecnicas

Decisoes confirmadas:

- FastAPI e o framework HTTP existente.
- A urgencia deve ser verificada deterministicamente antes do LLM.
- O backend deve controlar os estados da conversa.
- Segredos nao devem ser armazenados no codigo.
- A agenda deve ser a fonte de verdade para disponibilidade e reserva.
- As regras de cada clinica devem ficar em YAML validado, fora do codigo de dominio.

Decisoes pendentes:

- Redis e estrategia de fallback;
- provedor e modelo de LLM;
- canal de escalonamento humano;
- schema final da agenda;
- estrategia de deploy e observabilidade.
