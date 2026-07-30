# Plano de Estudo e Desenvolvimento — Lifeline-bot

Este documento guia o estudo e o desenvolvimento do projeto seguindo o briefing do CTO.

## Objetivo
- Entender o fluxo de atendimento (qualificação, urgência, agendamento).
- Garantir integração LLM segura (saída JSON), persistência (Redis/Postgres) e integração com Evolution/Google Calendar.

## Pré-requisitos
- Python 3.11+ (venv já incluído no repositório).
- Variáveis em `.env` configuradas (ver `.env.template`).
- Ter acesso às credenciais do Google (service account ou client_secret) se for testar calendar.

## Estrutura de estudos (ordem recomendada)
1. Ler o briefing: `docs/BRIEFING_Rauder_de_Azevedo_CTO.md` (compreender requisitos críticos).
2. Explorar pontos centrais do código:
   - `app/services/validador_fluxo.py` (máquina de estados)
   - `app/services/llm_service.py` (integração LLM / extração)
   - `app/repositories/schedule_repository.py` (reserva atômica)
   - `app/services/google_calendar_service.py` (integração Calendar)
   - `app/routers/webhook.py` (entrada webhook)
3. Rodar testes unitários e focados:
```bash
# usar o venv do projeto
venv\Scripts\activate
python -m pytest tests/test_validador_fluxo.py -q
python -m pytest tests/test_google_calendar_service.py -q
```
4. Testar fluxo end-to-end local (simulador):
```bash
python testar_modular.py
# ou
python tests/test_fluxo_completo.py
```
5. Configurar Google Calendar (opção A: service account)
   - Colocar JSON em `app/config/credentials.json.json` e montar em deploy
   - No `.env` habilitar `GOOGLE_CALENDAR_ENABLED=true` e apontar `GOOGLE_CREDENTIALS_FILE` e `GOOGLE_TOKEN_FILE`
6. Verificar a tabela `agendamentos` e popular horários de teste (ver `docker-compose` ou script de seed).

## Tarefas práticas e checkpoints
- Implementar/validar extração JSON do LLM: checar `llm_service.extract_structured` e testes em `tests/test_llm_service.py`.
- Garantir reserva atômica: revisar `reserve_slot` em `app/repositories/schedule_repository.py` e testar concorrência leve.
- Habilitar Calendar e testar `calendar_service.criar_evento()` com mock e com credenciais.
- Validar envio Evolution: revisar `app/services/evolution_service.py` e enviar mensagens de teste (usar `EVOLUTION_SEND_ENABLED=false` para dry-run).
- Criar/ajustar dashboard: `app/routers/dashboard.py` deve mostrar sessões e confirmações.

## Boas práticas e segurança
- Nunca versionar credenciais: adicione ao `.gitignore` se necessário.
- Use service accounts em produção ou secret manager para tokens OAuth.

## Recursos úteis
- Docs Google Calendar API: https://developers.google.com/calendar
- OpenAI/LLM: revisar instruções em `app/services/llm_service.py`

## Próximo passo sugerido
- Escolha uma tarefa do bloco "Tarefas práticas" para eu implementar ou detalhar (ex: escrever script seed, adicionar teste E2E com mock, ou documentar deploy com service account).

---
Arquivo criado para guiar o estudo e desenvolvimento do fluxo conforme o briefing.
