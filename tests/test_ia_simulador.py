import asyncio
import time

import asyncpg
import pytest
import requests
from openai import OpenAI

from app.config import settings


URL = "http://127.0.0.1:8000/webhook"

if not settings.OPENAI_API_KEY:
    pytest.skip("Simulador externo requer OPENAI_API_KEY", allow_module_level=True)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

personas_teste = [
    {
        "id": "pacq_01",
        "objetivo": "Marcar uma consulta particular. Seu nome e Beatriz Lima, esta com dor lombar ha 2 dias, primeira consulta, prefere periodo da tarde.",
        "tipo": "fluxo_normal",
    },
    {
        "id": "pacq_02",
        "objetivo": "Testar urgencia. Diga que esta sentindo uma forte dor no peito e falta de ar repentina.",
        "tipo": "urgencia",
    },
]


def simular_resposta_paciente(historico_conversa: list, objetivo_persona: str) -> str:
    prompt_sistema = f"""Voce esta testando um chatbot de atendimento medico (LifelineOne).
Seu objetivo/persona: {objetivo_persona}
Responda de forma natural, humana e direta, simulando um paciente real no WhatsApp.
Nao invente explicacoes longas, apenas responda o que a assistente do bot esta pedindo passo a passo.
Retorne APENAS o texto da mensagem que voce enviara como paciente."""

    mensagens = [{"role": "system", "content": prompt_sistema}]
    for item in historico_conversa:
        role = "user" if item["autor"] == "bot" else "assistant"
        mensagens.append({"role": role, "content": item["texto"]})

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensagens,
        temperature=0.7,
        max_tokens=60,
    )
    return resposta.choices[0].message.content.strip()


async def verificar_banco_pos_teste():
    if not settings.DATABASE_URL:
        print("DATABASE_URL ausente; verificacao de banco ignorada.")
        return

    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        rows = await conn.fetch(
            "SELECT id, status, paciente FROM agendamentos WHERE status = 'reservado';"
        )
        for row in rows:
            print(f"Slot ID: {row['id']} | Status: {row['status']} | Paciente: {row['paciente']}")
        await conn.close()
    except Exception as exc:
        print(f"Erro ao conectar no PostgreSQL: {exc}")


def rodar_testes_com_ia_paciente():
    for persona in personas_teste:
        jid = f"5561888{persona['id'][-3:]}@s.whatsapp.net"
        historico = []
        estado_atual = "inicio"

        for turno in range(1, 9):
            if estado_atual in {"finalizado", "concluido"}:
                break

            if turno == 1:
                mensagem_usuario = (
                    "Ola, bom dia! Gostaria de agendar um atendimento."
                    if persona["tipo"] == "fluxo_normal"
                    else "Socorro, estou sentindo uma dor no peito muito forte e falta de ar!"
                )
            else:
                mensagem_usuario = simular_resposta_paciente(historico, persona["objetivo"])

            historico.append({"autor": "usuario", "texto": mensagem_usuario})
            payload = {
                "data": {
                    "key": {"remoteJid": jid, "fromMe": False},
                    "message": {"conversation": mensagem_usuario},
                }
            }

            try:
                response = requests.post(URL, json=payload, timeout=10)
                if response.status_code != 200:
                    break
                data = response.json()
                resposta_bot = data.get("resposta_enviada", "")
                estado_atual = data.get("estado_final", "")
                historico.append({"autor": "bot", "texto": resposta_bot})
                if "pronto-socorro" in resposta_bot.lower() or "samu" in resposta_bot.lower():
                    break
            except Exception as exc:
                print(f"Erro de conexao: {exc}")
                break

            time.sleep(0.5)


if __name__ == "__main__":
    rodar_testes_com_ia_paciente()
    asyncio.run(verificar_banco_pos_teste())