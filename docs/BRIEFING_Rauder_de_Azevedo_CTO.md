LIFELINEONE — TECNOLOGIA COM IA

Briefing Rauder de Azevedo — CTO

Desafio técnico de trainee — Agente de IA para atendimento clínico via WhatsApp

1. Contexto e objetivo

Você vai construir, em 7 dias, um agente de inteligência artificial que atende pacientes de uma clínica pelo WhatsApp. O agente precisa qualificar o paciente (entender quem é e o que precisa), identificar se é um caso urgente, e agendar uma consulta automaticamente — sem intervenção humana no meio do processo.

Este não é um exercício teórico. O objetivo é que, ao final da semana, o fluxo completo funcione de ponta a ponta: paciente manda mensagem no WhatsApp → agente conversa com ele → consulta é marcada → paciente recebe confirmação.

Esperamos comprometimento e dedicação integral durante os 7 dias. É um prazo apertado de propósito: queremos ver como você aprende rápido, se vira com pouca informação e resolve problemas sozinho antes de pedir ajuda.

2. O que já está pronto (não é sua responsabilidade)

Toda a infraestrutura abaixo já está sendo cuidada pelo CTO. Você não precisa subir servidor, configurar Docker, criar instância da Evolution API nem gerenciar chaves de API. Seu foco é 100% em execução: lógica do agente, integração e fluxo de conversa.

Instância da Evolution API (WhatsApp) configurada e conectada a um número de teste

Webhook da Evolution API já apontando para o endereço que você vai receber

Chaves de API (OpenAI/Claude) já provisionadas e entregues a você

Banco de dados (PostgreSQL/Supabase) e Redis já disponíveis, com credenciais de acesso

Ambiente de deploy (Railway/Vercel) já configurado para receber seu projeto

Você vai receber um documento à parte com as credenciais e endpoints. Se algo de infraestrutura não estiver funcionando, me avise direto — não perca tempo tentando resolver isso sozinho.

3. O que é sua responsabilidade

Construir a API em Python com FastAPI que recebe as mensagens do WhatsApp (via webhook da Evolution API) e envia respostas

Construir o agente conversacional com LangChain, seguindo o briefing da IA na seção 5 deste documento

Implementar o fluxo de qualificação e agendamento (máquina de estados da conversa)

Persistir o estado da conversa (Redis) e os dados de agendamento (PostgreSQL)

Tratar erros e casos de borda (mensagens fora de ordem, respostas inesperadas do paciente, timeouts)

Fazer o deploy do seu projeto no ambiente já preparado e testar o fluxo real pelo WhatsApp

4. Cronograma diário

5. Briefing completo da IA (o que o agente precisa fazer)

Esta seção é a especificação do comportamento do agente. É o que você precisa transformar em prompt de sistema + lógica de estados no seu código. Leia com atenção antes de começar o Dia 3.

5.1 Persona e tom de voz

Nome do agente: assistente virtual da clínica (defina um nome amigável, ex: “Ana”, “Lia”)

Tom: acolhedor, claro e objetivo — nunca informal demais, nunca clínico/frio demais

Linguagem simples, frases curtas. Evitar jargão médico ou técnico

O agente nunca dá diagnóstico, nunca opina sobre gravidade de sintomas além de identificar urgência básica, e nunca substitui um profissional de saúde

Em caso de dúvida sobre o que responder, o agente deve pedir para o paciente repetir ou esclarecer — nunca inventar informação

5.2 Fluxo de qualificação — dados obrigatórios a coletar

O agente precisa coletar, nesta ordem, antes de oferecer horários:

Nome completo do paciente

Motivo da consulta / sintoma principal (texto livre, uma frase)

Se é particular ou tem convênio — e qual convênio, se tiver

Se já é paciente da clínica ou é a primeira consulta

Preferência de período (manhã/tarde) e, se possível, dia da semana

Cada resposta do paciente deve ser validada antes de avançar de etapa. Se a resposta não fizer sentido para a pergunta feita (ex: perguntou o nome e o paciente respondeu com um sintoma), o agente deve repetir a pergunta de forma educada, sem travar o fluxo.

5.3 Regra de urgência (crítico)

Esta regra tem que ser determinística, não pode depender só do LLM decidir livremente. Use uma checagem por palavras-chave ANTES de deixar o LLM responder.

Palavras/expressões que disparam escalonamento imediato: dor no peito, falta de ar, sangramento intenso, desmaio, perda de consciência, convulsão, dor muito forte, pensamento suicida, emergência

Se qualquer sinal de urgência for detectado, o agente PARA o fluxo de agendamento normal, orienta o paciente a procurar atendimento de emergência imediatamente (pronto-socorro / SAMU 192), e notifica um humano da clínica (defina o canal com o CTO — ex: mensagem interna, e-mail, alerta no Slack)

O agente nunca tenta 'agendar uma consulta normal' para um caso que ele mesmo identificou como urgente

5.4 Agendamento

Depois da qualificação completa, o agente consulta os horários disponíveis no banco (ver Dia 5) e oferece no máximo 3 opções por vez

Paciente escolhe respondendo com o número da opção ou repetindo o horário

Agente confirma o horário escolhido, marca como reservado no banco, e envia uma mensagem de confirmação com: nome do paciente, data, hora, e uma orientação simples (ex: chegar com 10 min de antecedência)

Se nenhum horário oferecido servir, o agente pergunta se o paciente quer ver mais opções ou prefere que a clínica entre em contato

5.5 Formato de saída esperado do LLM

Para facilitar a lógica de estados, force o LLM a responder em JSON estruturado internamente (não é o que o paciente vê — é o que seu backend processa), por exemplo:

{ "resposta_paciente": "texto que vai pro WhatsApp", "proximo_estado": "coletar_convenio", "dados_extraidos": { "nome": "Maria Silva" }, "urgente": false }

Isso evita que você precise 'adivinhar' o que o modelo respondeu — seu código lê o campo proximo_estado e decide o que fazer a seguir.

5.6 Exemplo de diálogo (referência)

Paciente: Oi, queria marcar uma consulta

Agente: Olá! Eu sou a Ana, assistente virtual da clínica. Posso te ajudar a agendar. Qual é o seu nome completo?

Paciente: João Pereira

Agente: Prazer, João! Me conta rapidamente o motivo da consulta ou o que você está sentindo.

Paciente: Dor de cabeça frequente há uma semana

Agente: Entendi. Você é particular ou tem convênio?

... (fluxo continua até oferecer horários e confirmar)

6. Critérios de avaliação

Funciona de ponta a ponta: mensagem real no WhatsApp até confirmação real de agendamento

Segue a regra de urgência corretamente, sem exceção

Código organizado o suficiente para outra pessoa entender o fluxo de estados

Capacidade de explicar as decisões técnicas tomadas (por que Redis, por que essa estrutura de estados, etc.)

Autonomia: quantas vezes precisou de ajuda e em quais pontos

7. Entrega final (dia 7)

Link do repositório com o código

Projeto rodando em produção no ambiente já preparado

Demonstração ao vivo comigo, com WhatsApp real

Breve explicação verbal do fluxo de estados e das decisões técnicas

Qualquer dúvida de infraestrutura (Evolution API, chaves, banco), me chame direto. Dúvidas de lógica e código, tente resolver sozinho primeiro — isso também está sendo avaliado.