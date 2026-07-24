# Google Calendar

A agenda sera integrada ao Google Calendar por OAuth de aplicativo instalado.

Configuracao:

- `GOOGLE_CALENDAR_ENABLED=false` por padrao;
- `GOOGLE_CALENDAR_ID=primary` por padrao;
- `GOOGLE_CREDENTIALS_FILE` aponta para o JSON OAuth local;
- `GOOGLE_TOKEN_FILE` armazena o token autorizado localmente.

O arquivo de credenciais e o token sao ignorados pelo Git. A primeira autorizacao, quando habilitada, abre o navegador local e cria `token.json`.

O adaptador em `app/services/google_calendar_service.py` ainda nao e chamado pela maquina de estados. Antes disso, devem ser definidos horario de funcionamento, duracao da consulta, fuso horario e regra para gerar os slots disponiveis.
