import asyncio
import sys
import os

# Garantir que o diretório do projeto esteja no sys.path para importar o pacote `app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services import session_repository, agendamento_repository
from app.services.validador_fluxo import processar_fluxo_atendimento


async def handle(remote_jid: str, texto: str):
    sess = await session_repository.obter_sessao_async(remote_jid)
    estado = sess.get("estado", "inicio")
    resposta, proximo, dados_atualizados = await processar_fluxo_atendimento(
        estado, texto, sess
    )
    dados_atualizados["estado"] = proximo
    await session_repository.salvar_sessao_async(remote_jid, dados_atualizados)
    if proximo == "concluido":
        await agendamento_repository.salvar_agendamento_async(remote_jid, dados_atualizados)

    print("\n--- RESULTADO ---")
    print("RESPOSTA:", resposta)
    print("PROXIMO_ESTADO:", proximo)
    print("DADOS:", dados_atualizados)
    print("-----------------\n")


def main():
    remote = input("remote_jid [test@server]: ") or "test@server"
    print("Digite mensagens para simular o fluxo. Ctrl+C para sair.")
    try:
        while True:
            texto = input("> ")
            if not texto.strip():
                continue
            asyncio.run(handle(remote, texto))
    except KeyboardInterrupt:
        print("\nEncerrando interativo.")


if __name__ == "__main__":
    main()
