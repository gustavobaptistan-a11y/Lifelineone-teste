# Google Calendar

A agenda esta integrada ao Google Calendar por OAuth de aplicativo instalado.

Configuracao:

- `GOOGLE_CALENDAR_ENABLED=false` por padrao;
- `GOOGLE_CALENDAR_ID=primary` por padrao;
- `GOOGLE_CREDENTIALS_FILE` aponta para o JSON OAuth local;
- `GOOGLE_TOKEN_FILE` armazena o token autorizado localmente.

O arquivo de credenciais e o token sao ignorados pelo Git. A primeira autorizacao, quando habilitada, abre o navegador local e cria `token.json`.

O adaptador em `app/services/google_calendar_service.py` ja e chamado pela maquina de estados de agendamento em `app/services/validador_fluxo.py`.

Fluxo de calendario:

- quando `GOOGLE_CALENDAR_ENABLED=true`, o sistema lista eventos existentes para evitar conflitos;
- ao selecionar o horario, o evento e criado no Google Calendar usando `calendar_service.criar_evento(...)`;
- se o Google Calendar estiver desabilitado, o sistema ainda gera horarios disponiveis localmente com base em `config/clinic.yaml`.

Requisitos:

- `GOOGLE_CREDENTIALS_FILE` deve conter as credenciais de OAuth do Google Calendar;
- `GOOGLE_TOKEN_FILE` sera criado apos autorizacao inicial;
- `GOOGLE_CALENDAR_ID` pode ser `primary` ou o ID de agenda desejado.
