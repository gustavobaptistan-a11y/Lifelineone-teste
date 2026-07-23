import requests
import time
from dotenv import load_dotenv
from openai import OpenAI
from app.config import settings

load_dotenv()

URL = "http://127.0.0.1:8000/webhook"
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# 5 personas simuladas de pacientes com cenários variados
personas_teste = [
    {
        "id": "pac_01",
        "nome": "Beatriz Lima",
        "objetivo": "Marcar consulta particular para dor lombar há 2 dias. Primeira consulta, prefere período da tarde.",
        "tipo": "fluxo_normal"
    },
    {
        "id": "pac_02",
        "nome": "Carlos Eduardo",
        "objetivo": "Marcar consulta de rotina pelo convênio Unimed. É retorno, prefere período da manhã.",
        "tipo": "fluxo_normal"
    },
    {
        "id": "pac_03",
        "nome": "Fernanda Souza",
        "objetivo": "Marcar consulta particular para enxaqueca frequente. Primeira consulta, prefere período da manhã.",
        "tipo": "fluxo_normal"
    },
    {
        "id": "pac_04",
        "nome": "Lucas Martins",
        "objetivo": "Marcar consulta pelo convênio Amil para check-up anual. É retorno, prefere período da tarde.",
        "tipo": "fluxo_normal"
    },
    {
        "id": "pac_05",
        "nome": "Emergencia Teste",
        "objetivo": "Relatar sintomas graves de urgência: dor no peito muito forte e falta de ar repentina.",
        "tipo": "urgencia"
    }
]

def simular_resposta_paciente(historico_conversa: list, persona: dict) -> str:
    prompt_sistema = f"""Você é o paciente {persona['nome']} testando um chatbot médico.
Seu objetivo/perfil: {persona['objetivo']}
Responda de forma natural, humana e direta, simulando um paciente real no WhatsApp.
Responda apenas o que a atendente do bot está pedindo no turno atual.
Retorne APENAS o texto da mensagem que você enviará como paciente."""

    mensagens = [{"role": "system", "content": prompt_sistema}]
    for h in historico_conversa:
        mensagens.append({"role": "user" if h["autor"] == "bot" else "assistant", "content": h["texto"]})

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensagens,
        temperature=0.7,
        max_tokens=60
    )
    return resposta.choices[0].message.content.strip()

def rodar_testes_5_pacientes():
    print("🚀 Iniciando testes com a IA Simuladora para 5 Pacientes...\n")
    
    for idx_p, persona in enumerate(personas_teste, 1):
        print(f"==================================================")
        print(f"👤 Paciente {idx_p}/5: {persona['nome']} ({persona['id']})")
        print(f"🎯 Objetivo: {persona['objetivo']}")
        print(f"==================================================")
        
        jid = f"5561998{idx_p:02d}@s.whatsapp.net"
        historico = []
        estado_atual = "inicio"
        
        for turno in range(1, 8):
            if estado_atual == "finalizado":
                print(f"🏁 Fluxo concluído com sucesso para {persona['nome']}!\n")
                break
                
            if turno == 1:
                if persona['tipo'] == "urgencia":
                    mensagem_usuario = "Socorro, estou sentindo uma dor no peito muito forte e falta de ar!"
                else:
                    mensagem_usuario = "Olá, bom dia! Gostaria de agendar um atendimento."
            else:
                mensagem_usuario = simular_resposta_paciente(historico, persona)
                
            historico.append({"autor": "usuario", "texto": mensagem_usuario})
            
            payload = {
                "data": {
                    "key": {"remoteJid": jid, "fromMe": False},
                    "message": {"conversation": mensagem_usuario}
                }
            }
            
            try:
                resp = requests.post(URL, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    resposta_bot = data.get('resposta_enviada', '')
                    estado_atual = data.get('estado_final', '')
                    
                    print(f"  [Turno {turno}] 👤 {persona['nome']}: '{mensagem_usuario}'")
                    print(f"           🤖 Bot Lifeline: '{resposta_bot[:90]}...'")
                    print(f"           📍 Estado: {estado_atual}\n")
                    
                    historico.append({"autor": "bot", "texto": resposta_bot})
                    
                    if "urgencia" in estado_atual or "pronto-socorro" in resposta_bot.lower():
                        print(f"🚨 Protocolo de Urgência acionado com sucesso para {persona['nome']}!\n")
                        break
                else:
                    print(f"  [Turno {turno}] 🔴 Erro HTTP {resp.status_code}: {resp.text}")
                    break
            except Exception as e:
                print(f"  [Turno {turno}] ❌ Erro de conexão: {e}")
                break
            
            time.sleep(0.4)

if __name__ == "__main__":
    rodar_testes_5_pacientes()
