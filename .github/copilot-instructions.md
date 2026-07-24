# Instrucoes do projeto

## Escopo

Este repositorio e um backend FastAPI para atendimento clinico via WhatsApp.

## Regras de trabalho

- Ler o fluxo e os usos antes de editar.
- Preservar compatibilidade e arquivos existentes.
- Fazer uma tarefa por vez.
- Validar cada alteracao com o teste mais focado disponivel.
- Nao expor ou imprimir credenciais.
- Nao versionar `.env`, bancos locais, binarios ou ambientes virtuais.
- Manter a urgencia deterministica e anterior ao LLM.
- Manter estados e regras de negocio no backend.
- Nao permitir diagnostico medico pelo agente.
- Atualizar a documentacao quando contratos ou fluxos mudarem.

## Validacao

Usar o ambiente virtual local e executar validacoes focadas antes da suite completa. Integracoes externas devem ser mockadas nos testes automatizados.
