# Status do Briefing vs Projeto

Este documento compara o briefing do CTO com o estado atual do projeto. Ele deve ser usado como guia antes de novas alteracoes de codigo.

## Resumo executivo

O projeto ja possui o nucleo do backend e do atendimento automatizado: FastAPI, webhook, maquina de estados, deteccao deterministica de urgencia, persistencia de sessao, persistencia de agendamento, integracao Evolution e adaptador Google Calendar.

Ainda nao deve ser considerado entrega final do briefing enquanto nao houver validacao real ponta a ponta em ambiente publico: WhatsApp real -> webhook publico -> conversa completa -> reserva persistida -> confirmacao enviada ao paciente.

## Comparativo

| Requisito do briefing | Status | Evidencia | Observacao |
| --- | --- | --- | --- |
| API Python com FastAPI | Pronto | `main.py`, `app/routers/webhook.py` | App registra webhook, admin e dashboard. |
| Receber mensagens Evolution/WhatsApp | Pronto parcial | `POST /webhook` | Contrato `messages.upsert` coberto por testes; falta validacao real com webhook publico. |
| Enviar respostas pelo WhatsApp | Pronto parcial | `app/services/evolution_service.py` | Cliente usa `EVOLUTION_INSTANCE_NAME` e valida configuracao; falta validar envio real em WhatsApp. |
| Maquina de estados da conversa | Pronto | `app/services/validador_fluxo.py` | Fluxo cobre nome, sintoma, convenio, primeira consulta, periodo, horarios e conclusao. |
| Validar respostas antes de avancar | Pronto parcial | `tests/test_validador_fluxo.py` | Ha validacoes principais; ainda faltam mais casos fora de ordem e mensagens duplicadas. |
| Urgencia deterministica antes do LLM | Pronto | `verificar_urgencia()` | Regra roda antes da extracao LLM e interrompe o fluxo. |
| Notificar humano em urgencia | Pendente | Nao encontrado | Briefing exige canal humano; hoje o fluxo orienta SAMU/pronto-socorro, mas nao notifica equipe. |
| LLM com saida JSON estruturada | Pronto parcial | `app/services/llm_service.py` | Usa OpenAI SDK direto; briefing cita LangChain. Falta decidir manter SDK ou adaptar. |
| Persistir sessao em Redis | Pronto parcial | `app/services/session_repository.py` | Redis suportado quando habilitado, com fallback. Falta validacao em ambiente real. |
| Persistir agendamento em PostgreSQL | Pronto parcial | `app/services/agendamento_repository.py`, `schedule_repository.py` | Persistencia existe; falta validar concorrencia e schema real em producao. |
| Reserva atomica de horario | Pronto parcial | `schedule_repository.reserve_slot()` | Usa `WHERE status = 'disponivel'`; falta teste forte de concorrencia. |
| Google Calendar | Extra/parcial | `app/services/google_calendar_service.py` | Nao e requisito central do briefing, mas agrega. Precisa evitar OAuth interativo em producao. |
| Deploy em producao | Pendente | `docs/10-deploy.md` | Infra externa; falta evidencia de URL publica e health check. |
| Teste real WhatsApp | Pendente | `README.md` | Checklist ainda nao marcado. |
| Demonstracao final | Pendente | Briefing | Depende de deploy e teste real. |

## Riscos atuais

- Arquivos locais com dados de teste foram removidos do indice do Git e ignorados: `sessions.json`, `agendamentos_db.json`, `app/services/sessions_db.json`.
- Credenciais locais devem continuar somente em `.env`, `credentials.json` e `token.json`, todos ignorados.
- A suite completa teve bloqueio de permissao em pastas temporarias no Windows/sandbox; os testes focados de webhook e fluxo passaram.
- Ha mudancas locais nao commitadas em varios arquivos; novas alteracoes devem continuar pequenas e verificadas.

## Proxima sequencia segura

1. Estabilizar testes para rodarem sem `.env` real e sem chamadas externas.
2. Corrigir Evolution para usar explicitamente `EVOLUTION_INSTANCE_NAME` no envio real.
3. Adicionar `/health` sem expor segredos.
4. Adicionar alerta humano para urgencia ou documentar canal definido pelo CTO.
5. Validar E2E local com mocks.
6. Validar WhatsApp real e deploy publico.