# Documento de Contexto Técnico - Projeto Lifeline-bot

Este documento centraliza as informações cruciais sobre o projeto, servindo como guia para desenvolvimento, manutenção e onboarding de novos membros da equipe.

## 1. Objetivo do Projeto

O objetivo principal é desenvolver um agente de IA ("Ana") que opera via WhatsApp para realizar o agendamento de consultas médicas para a clínica LifelineOne. O agente deve qualificar o paciente, verificar a urgência e, se não for um caso emergencial, guiá-lo através de um fluxo de agendamento até a confirmação de um horário.

## 2. Arquitetura

O projeto é construído sobre uma arquitetura de microsserviço com os seguintes componentes:

- **Backend**: Uma aplicação **FastAPI** (Python) que expõe um endpoint de webhook para receber mensagens do WhatsApp.
- **Banco de Dados**: **PostgreSQL** é utilizado para armazenar e gerenciar os horários de consulta, garantindo a atomicidade das reservas.
- **Gerenciamento de Sessão**: **Redis** é responsável por persistir o estado da conversa de cada paciente, com um fallback para um dicionário em memória para desenvolvimento local.
- **Inteligência Artificial**: A biblioteca **LangChain** integra-se com um modelo de linguagem da **OpenAI** (como o GPT-4o-mini) para interpretar as respostas do usuário de forma estruturada.
- **Comunicação WhatsApp**: A **Evolution API** atua como um gateway para enviar e receber mensagens do WhatsApp.

## 3. Fluxo Completo de Agendamento

O fluxo de interação com o paciente é gerenciado por uma máquina de estados determinística no backend, seguindo uma ordem precisa:

1.  **Saudação Inicial**: O usuário envia a primeira mensagem.
2.  **Verificação de Urgência**: O sistema primeiro verifica se a mensagem contém palavras-chave de emergência (ex: "dor no peito", "desmaio").
    - **Se Urgente**: O fluxo é interrompido, o paciente é instruído a procurar o pronto-socorro/SAMU, e um alerta humano é (opcionalmente) disparado.
    - **Se Não Urgente**: O fluxo de agendamento continua.
3.  **Coletar Nome**: O agente "Ana" se apresenta e pergunta o nome completo do paciente.
4.  **Coletar Motivo**: Pergunta o motivo da consulta ou os sintomas.
5.  **Coletar Convênio**: Pergunta se o atendimento é particular ou por convênio.
6.  **Coletar Status de Paciente**: Verifica se é a primeira consulta ou se a pessoa já é paciente.
7.  **Coletar Preferência de Horário**: Pergunta a preferência de período (manhã ou tarde).
8.  **Apresentar Opções**: O sistema consulta os horários disponíveis no PostgreSQL para o período informado e os apresenta ao paciente como uma lista numerada.
9.  **Confirmar Horário**: O paciente escolhe uma das opções.
10. **Reserva Atômica**: O sistema tenta reservar o horário no banco de dados.
    - **Sucesso**: O horário é marcado como "reservado" no banco de dados.
    - **Falha (horário já ocupado)**: O sistema informa que o horário ficou indisponível e apresenta novas opções.
11. **Agendamento Confirmado**: O agente confirma o nome, dia e hora do agendamento e envia uma instrução final (ex: chegar com antecedência).

## 4. Responsabilidades dos Arquivos

- `main.py`: Ponto de entrada da aplicação FastAPI. Define o endpoint `/webhook`, gerencia as conexões (DB, Redis), orquestra o fluxo principal, e lida com o envio de respostas via Evolution API.
- `app/flow.py`: Contém a lógica da máquina de estados. Cada função (`_handle_...`) representa uma etapa do fluxo, validando a entrada do usuário e determinando a próxima etapa.
- `app/db.py` (implícito): Módulo para interagir com o PostgreSQL, contendo funções para buscar e reservar horários.
- `app/models.py` (implícito): Define os modelos de dados Pydantic, como `SessaoPaciente`, que estruturam as informações da sessão e os dados extraídos.
- `teste_envio.py`: Script de simulação para testar o fluxo de conversação de ponta a ponta localmente, sem depender do WhatsApp.
- `requirements.txt`: Lista as dependências Python do projeto.
- `.env` / `.env.example`: Arquivos para gerenciar variáveis de ambiente (chaves de API, URLs de conexão).
- `README.md`: Documentação geral do projeto, com instruções de instalação e execução.
- `BRIEFING_COMPLIANCE.md`: Documento que mapeia os requisitos do projeto com o que já foi implementado.

## 5. Dependências Principais

- `fastapi`: Framework web para a construção da API.
- `uvicorn`: Servidor ASGI para rodar a aplicação FastAPI.
- `psycopg2-binary`: Driver para conexão com o banco de dados PostgreSQL.
- `redis`: Cliente para conexão com o servidor Redis.
- `httpx`: Cliente HTTP assíncrono para fazer requisições às APIs externas.
- `langchain-openai`: Biblioteca para integração com os modelos da OpenAI.
- `pydantic`: Para validação de dados e configurações.
- `python-dotenv`: Para carregar variáveis de ambiente de um arquivo `.env`.

## 6. APIs Utilizadas

- **Evolution API**: Para comunicação (envio de mensagens) com a plataforma WhatsApp.
- **OpenAI API**: Para acesso aos modelos de linguagem que interpretam as mensagens dos usuários.

## 7. Padrões de Código e Convenções

- **Código Assíncrono**: Uso de `async/await` para operações de I/O, como chamadas de API e, idealmente, para interações com o banco de dados.
- **Máquina de Estados Determinística**: O fluxo da conversa é controlado pelo backend (`app/flow.py`), não pelo LLM. O LLM atua como um extrator de informações, mas a transição de estados é previsível e gerenciada pelo código.
- **Saída Estruturada do LLM**: O modelo de linguagem é instruído a retornar um JSON com uma estrutura pré-definida (`RespostaAgente`), garantindo previsibilidade na extração de dados.
- **Gerenciamento de Configuração**: As credenciais e configurações sensíveis são gerenciadas exclusivamente por meio de variáveis de ambiente, seguindo as melhores práticas do "Twelve-Factor App".
- **Modo de Desenvolvimento Local**: A variável `LOCAL_MODE` permite rodar e testar o projeto sem a necessidade de chaves de API reais, usando fallbacks em memória.

## 8. Regras de Negócio Críticas

1.  **Urgência Precede Tudo**: A verificação de urgência é determinística (baseada em palavras-chave) e executada **antes** de qualquer chamada ao LLM. Casos de emergência interrompem imediatamente o fluxo de agendamento.
2.  **O Backend é a Fonte da Verdade**: A máquina de estados no backend, e não o LLM, define o progresso da conversa e o `proximo_estado`.
3.  **Reserva Atômica**: A reserva de um horário no PostgreSQL é feita com uma condição (`WHERE status = 'disponivel'`) para evitar que o mesmo horário seja agendado por duas pessoas simultaneamente (condição de corrida).
4.  **Sem Diagnóstico Médico**: O agente é estritamente proibido de fornecer qualquer tipo de diagnóstico ou conselho médico. Sua função é limitada ao agendamento.

## 9. Decisões Arquiteturais

- **Separação de Responsabilidades**: A lógica de negócio (máquina de estados) foi separada da infraestrutura web (FastAPI) e da camada de IA (LangChain), facilitando a manutenção e os testes.
- **Controle Centralizado vs. Liberdade do LLM**: Optou-se por um fluxo controlado pelo backend para garantir a conformidade com os requisitos e a previsibilidade do processo. O LLM é uma ferramenta de NLU (Natural Language Understanding), não um tomador de decisões de negócio.
- **Persistência de Sessão com Fallback**: O uso de Redis para produção garante escalabilidade e persistência entre reinicializações do serviço, enquanto o fallback para um dicionário em memória simplifica o desenvolvimento e os testes locais.
- **Health Check Detalhado**: O endpoint `/health` fornece um diagnóstico claro do estado do serviço, informando quais integrações estão ativas e se o sistema está pronto para operar em produção, o que é vital para depuração e monitoramento.