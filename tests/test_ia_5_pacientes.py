import time

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
        "id": "pac_01",
        "nome": "Beatriz Lima",
        "objetivo": "Marcar consulta particular para dor lombar ha 2 dias. Primeira consulta, prefere periodo da tarde.",
        "tipo": "fluxo_normal",
    },
    {
        "id": "pac_02",
        "nome": "Carlos Eduardo",
        "objetivo": "Marcar consulta de rotina pelo convenio Unimed. E retorno, prefere periodo da manha.",
        "tipo": "fluxo_normal",
    },
    {
        "id": "pac_03",
        "nome": "Fernanda Souza",
        "objetivo": "Marcar consulta particular para enxaqueca frequente. Primeira consulta, prefere periodo da manha.",
        "tipo": "fluxo_normal",
    },
    {
        "id": "pac_04",
        "nome": "Lucas Martins",
        "objetivo": "Marcar consulta pelo convenio Amil para check-up anual. E retorno, prefere periodo da tarde.",
        "tipo": "fluxo_normal",
    },
    {
        "id": "pac_05",
        "nome": "Emergencia Teste",
        "objetivo": "Relatar sintomas graves de urgencia: dor no peito muito forte e falta de ar repentina.",
        "tipo": "urgencia",
    },
]


def simular_resposta_paciente(historico_conversa: list, persona: dict) -> str:
    prompt_sistema = f"""Voce e o paciente {persona['nome']} testando um chatbot medico.
Seu objetivo/perfil: {persona['objetivo']}
Responda de forma natural, humana e direta, simulando um paciente real no WhatsApp.
Responda apenas o que a atendente do bot esta pedindo no turno atual.
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


def rodar_testes_5_pacientes():
    for idx_p, persona in enumerate(personas_teste, 1):
        jid = f"5561998{idx_p:02d}@s.whatsapp.net"
        historico = []
        estado_atual = "inicio"

        for turno in range(1, 8):
            if estado_atual in {"finalizado", "concluido"}:
                break

            if turno == 1:
                mensagem_usuario = (
                    "Socorro, estou sentindo uma dor no peito muito forte e falta de ar!"
                    if persona["tipo"] == "urgencia"
                    else "Ola, bom dia! Gostaria de agendar um atendimento."
                )
            else:
                mensagem_usuario = simular_resposta_paciente(historico, persona)

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
                if "urgencia" in estado_atual or "pronto-socorro" in resposta_bot.lower():
                    break
            except Exception as exc:
                print(f"Erro de conexao: {exc}")
                break

            time.sleep(0.4)


if __name__ == "__main__":
    rodar_testes_5_pacientes()