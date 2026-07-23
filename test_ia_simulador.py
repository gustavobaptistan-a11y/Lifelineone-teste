import requests
import time
import asyncio
import asyncpg
from openai import OpenAI
from app.config import settings

URL = "http://127.0.0.1:8000/webhook"
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Personas que a IA Simuladora vai adotar para testar o bot
personas_teste = [
    {
        "id": "pacq_01",
        "objetivo": "Marcar uma consulta particular. Seu nome é Beatriz Lima, está com dor lombar há 2 dias, primeira consulta, prefere período da tarde.",
        "tipo": "fluxo_normal"
    },
    {
        "id": "pacq_02",
        "objetivo": "Testar urgência. Diga que está sentindo uma forte dor no peito e falta de ar repentina.",
        "tipo": "urgencia"
    }
]

def simular_resposta_paciente(historico_conversa: list, objetivo_persona: str) -> str:
    """Usa uma IA para gerar a próxima resposta realista do paciente com base no histórico."""
    prompt_sistema = f"""Você está testando um chatbot de atendimento médico (LifelineOne).
Seu objetivo/persona: {objetivo_persona}
Responda de forma natural, humana e direta, simulando um paciente real no WhatsApp. 
Não invente explicações longas, apenas responda o que a assistente do bot está pedindo passo a passo (como seu nome, sintoma, convênio, etc.).
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

async def verificar_banco_pos_teste():
    print("\n" + "="*50)
    print("📊 VERIFICAÇÃO DE PERSISTÊNCIA NO BANCO (SUPABASE)")
    print("="*50)
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        rows = await conn.fetch("SELECT id, status, paciente FROM agendamentos WHERE status = 'reservado';")
        if rows:
            print(f"✅ SUCESSO! Agendamentos salvos no banco:")
            for r in rows:
                print(f"   - Slot ID: {r['id']} | Status: {r['status']} | Paciente: {r['paciente']}")
        else:
            print("⚠️ Nenhum agendamento 'reservado' encontrado.")
        await conn.close()
    except Exception as e:
        print(f"❌ Erro ao conectar no PostgreSQL: {e}")

def rodar_testes_com_ia_paciente():
    print("🚀 Iniciando testes em massa com IA Simuladora de Pacientes...\n")
    
    for persona in personas_teste:
        print(f"--------------------------------------------------")
        print(f"🤖 [Iniciando Teste] Persona ID: {persona['id']} | Tipo: {persona['tipo']}")
        print(f"🎯 Objetivo: {persona['objetivo']}")
        print(f"--------------------------------------------------")
        
        jid = f"5561888{persona['id'][-3:]}@s.whatsapp.net"
        historico = []
        estado_atual = "inicio"
        
        # Roda a conversação em turnos (máximo de 8 interações por paciente)
        for turno in range(1, 9):
            if estado_atual == "finalizado":
                print(f"🏁 Fluxo concluído com sucesso para {persona['id']}!\n")
                break
                
            # A IA do Paciente gera a mensagem com base na conversa
            if turno == 1:
                mensagem_usuario = "Olá, bom dia! Gostaria de agendar um atendimento." if persona['tipo'] == "fluxo_normal" else "Socorro, estou sentindo uma dor no peito muito forte e falta de ar!"
            else:
                mensagem_usuario = simular_resposta_paciente(historico, persona['objetivo'])
                
            historico.append({"autor": "usuario", "texto": mensagem_usuario})
            
            # Envia para o Webhook do Bot
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
                    
                    print(f"  [Turno {turno}] 👤 Paciente IA: '{mensagem_usuario}'")
                    print(f"           🤖 Bot Lifeline: '{resposta_bot[:90]}...'")
                    print(f"           📍 Estado Atual: {estado_atual}\n")
                    
                    historico.append({"autor": "bot", "texto": resposta_bot})
                    
                    # Se caiu em urgência, encerra o teste desta persona com sucesso de segurança
                    if "pronto-socorro" in resposta_bot.lower() or "samu" in resposta_bot.lower():
                        print(f"🚨 Protocolo de Urgência acionado perfeitamente para {persona['id']}!\n")
                        break
                else:
                    print(f"  [Turno {turno}] 🔴 Erro HTTP {resp.status_code}")
                    break
            except Exception as e:
                print(f"  [Turno {turno}] ❌ Erro de conexão: {e}")
                break
                
            time.sleep(0.5)

if __name__ == "__main__":
    rodar_testes_com_ia_paciente()
    asyncio.run(verificar_banco_pos_teste())
