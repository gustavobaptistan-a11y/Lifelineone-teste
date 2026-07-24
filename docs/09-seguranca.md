# Seguranca

Segredos devem existir somente em variaveis de ambiente ou no provedor de deploy. `.env` e `config_backup/` sao arquivos locais ignorados pelo Git.

Riscos conhecidos que exigem tratamento futuro:

- credenciais expostas anteriormente devem ser rotacionadas;
- webhook sem autenticacao ou assinatura verificada;
- ausencia de rate limit;
- mensagens proprias ainda nao filtradas;
- detalhes de excecao podem ser devolvidos ao cliente;
- logs devem evitar tokens, dados clinicos e identificadores desnecessarios.
