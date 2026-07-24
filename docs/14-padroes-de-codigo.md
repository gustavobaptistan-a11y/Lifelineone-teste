# Padroes de codigo

Convencoes atuais observadas:

- Python com FastAPI.
- Configuracao por variaveis de ambiente.
- Funcoes e classes em portugues e ingles misturados.
- Servicos agrupados em `app/services`.
- Testes e simuladores em `tests/`.

Padroes desejados:

- responsabilidades pequenas e explicitas;
- contratos Pydantic nas bordas;
- erros de dominio separados de erros de infraestrutura;
- logs estruturados sem dados sensiveis;
- testes deterministas e isolados;
- nenhuma dependencia implicita de arquivos locais.
