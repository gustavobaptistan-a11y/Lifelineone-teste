# Fluxo da aplicacao

1. FastAPI recebe um evento em `POST /webhook`.
2. O router extrai `remoteJid` e o texto da mensagem.
3. A sessao e carregada pelo repositorio de sessoes.
4. A urgencia e verificada antes da maquina de estados.
5. O estado atual processa a resposta do paciente.
6. O novo estado e salvo.
7. O endpoint devolve JSON ao chamador.

Estados de qualificacao atuais:

- `inicio`;
- `aguardando_nome`;
- `aguardando_sintoma`;
- `aguardando_convenio`;
- `aguardando_primeira_consulta`;
- `aguardando_preferencia_horario`;
- `aguardando_horario`;
- `concluido`;
- `urgencia_detectada`.

As respostas sao validadas localmente antes de avancar. A verificacao de urgencia continua sendo executada antes de qualquer estado.

Limitacao atual: a resposta ainda nao e enviada de volta ao WhatsApp pelo fluxo principal.
