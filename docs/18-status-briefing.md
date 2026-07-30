# Status do Briefing vs Projeto

Este documento compara o briefing do CTO com o estado atual do projeto. Ele deve ser usado como guia antes de novas alteracoes de codigo.

Ultima atualizacao: 30/07/2026.

## Resumo executivo

O projeto ja possui o nucleo do backend e do atendimento automatizado: FastAPI, webhook, maquina de estados, deteccao deterministica e por LLM de urgencia, alerta interno de urgencia, persistencia de sessao, persistencia de agendamento, integracao Evolution e adaptador Google Calendar.

Estimativa atual: cerca de 75% do briefing funcional esta implementado no codigo. Para producao real, a prontidao fica em torno de 60%, porque ainda dependem de validacao externa o WhatsApp real, webhook publico, credenciais, ambiente de deploy e teste ponta a ponta.

Ainda nao deve ser considerado entrega final do briefing enquanto nao houver validacao real ponta a ponta em ambiente publico: WhatsApp real -> webhook publico -> conversa completa -> reserva persistida -> confirmacao enviada ao paciente.

## Comparativo

| Requisito do briefing | Status | Evidencia | Observacao |
| --- | --- | --- | --- |
| API Python com FastAPI | Pronto | `main.py`, `app/routers/webhook.py` | App registra webhook, admin e dashboard. |
| Receber mensagens Evolution/WhatsApp | Pronto parcial | `POST /webhook` | Contrato `messages.upsert` coberto por testes; falta validacao real com webhook publico. |
| Enviar respostas pelo WhatsApp | Pronto parcial | `app/services/evolution_service.py` | Cliente usa `EVOLUTION_INSTANCE_NAME`, header `apikey` e payload padronizado; falta validar envio real em WhatsApp. |
| Maquina de estados da conversa | Pronto | `app/services/validador_fluxo.py` | Fluxo cobre nome, sintoma, convenio, primeira consulta, periodo, horarios e conclusao. |
| Refinamento humanizado da conversa | Pronto parcial | `app/services/validador_fluxo.py` | Nome e normalizado, convenio generico nao avanca, textos de acolhimento e confirmacao foram refinados. |
| Validar respostas antes de avancar | Pronto parcial | `tests/test_validador_fluxo.py` | Ha validacoes principais; ainda faltam mais casos fora de ordem, mensagens duplicadas e cancelamento. |
| Urgencia deterministica antes do LLM | Pronto | `verificar_urgencia()` | Regra roda antes da extracao LLM e interrompe o fluxo. |
| Notificar humano em urgencia | Pronto parcial | `app/services/alert_service.py` | Hoje registra alerta interno em log estruturado; falta definir canal real com o CTO. |
| LLM com saida JSON estruturada | Pronto parcial | `app/services/llm_service.py` | Usa OpenAI SDK direto; briefing cita LangChain. Falta decidir manter SDK ou adaptar. |
| Persistir sessao em Redis | Pronto parcial | `app/services/session_repository.py` | Redis suportado quando habilitado, com fallback. Falta validacao em ambiente real. |
| Persistir agendamento em PostgreSQL | Pronto parcial | `app/services/agendamento_repository.py`, `schedule_repository.py` | Persistencia existe; falta validar concorrencia e schema real em producao. |
| Reserva atomica de horario | Pronto parcial | `schedule_repository.reserve_slot()` | Usa `WHERE status = 'disponivel'`; falta teste forte de concorrencia. |
| Google Calendar | Extra/parcial | `app/services/google_calendar_service.py` | Nao e requisito central do briefing, mas agrega. Precisa evitar OAuth interativo em producao. |
| Health check para deploy | Pronto | `GET /health`, `tests/test_health.py` | Endpoint retorna apenas flags booleanas e nao expoe segredos. |
| Deploy em producao | Pendente | `docs/10-deploy.md` | Infra externa; falta evidencia de URL publica. |
| Teste real WhatsApp | Pendente | `README.md` | Checklist ainda nao marcado. |
| Demonstracao final | Pendente | Briefing | Depende de deploy e teste real. |

## Riscos atuais

- Arquivos locais com dados de teste foram removidos do indice do Git e ignorados: `sessions.json`, `agendamentos_db.json`, `app/services/sessions_db.json`.
- Credenciais locais devem continuar somente em `.env`, `credentials.json` e `token.json`, todos ignorados.
- O alerta humano de urgencia ainda e log interno; para producao, precisa canal operacional definido e monitorado.
- Novas alteracoes devem continuar pequenas, testadas e commitadas por etapa.

## Proxima sequencia segura

1. Estabilizar testes para rodarem sem `.env` real e sem chamadas externas.
2. Definir com o CTO o canal real do alerta humano de urgencia.
3. Validar E2E local com mocks.
4. Validar WhatsApp real e deploy publico.
