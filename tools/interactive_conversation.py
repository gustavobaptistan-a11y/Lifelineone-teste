import argparse
import asyncio
import sys
import os
import time
import random

# Garantir que o diretório do projeto esteja no sys.path para importar o pacote `app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services import session_repository
from app.services.agendamento_repository import agendamento_repository
from app.services.validador_fluxo import processar_fluxo_atendimento

MIN_RESPONSE_DELAY = 0.0
MAX_RESPONSE_DELAY = 0.0


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


async def reset_sessions():
    sessions = await session_repository.obter_todas_sessoes_async()
    jids = {sess["remote_jid"] for sess in sessions}
    for jid in jids:
        await session_repository.resetar_sessao_async(jid)
    return len(jids)


def main():
    parser = argparse.ArgumentParser(description="Simulador de conversação Lifeline");
    parser.add_argument("--reset", action="store_true", help="Resetar todas as sessões antes de iniciar")
    parser.add_argument("--remote", default="test@server", help="remote_jid do usuário")
    args = parser.parse_args()

    if args.reset:
        print("Resetando sessões existentes...")
        quantidade = asyncio.run(reset_sessions())
        print(f"Sessões resetadas: {quantidade}")

    remote = args.remote
    print(f"Iniciando simulação de IA para remote_jid={remote}")
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
