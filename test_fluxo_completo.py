import requests
import asyncio
import asyncpg
from app.config import settings

URL = "http://127.0.0.1:8000/webhook"
jid_teste = "5561988887777@s.whatsapp.net"

passos_conversa = [
    "Olá, gostaria de marcar uma consulta",
    "Carlos Eduardo Mendes",
    "Dor nas costas frequente há três dias",
    "Particular",
    "Sim, primeira consulta",
    "Prefiro no período da tarde"
]

async def verificar_banco():
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        rows = await conn.fetch("SELECT id, status, paciente FROM agendamentos;")
        print("\n📊 Estado Atual da Agenda no Supabase:")
        for r in rows:
            print(f"   Slot ID {r['id']} | Status: {r['status']} | Paciente: {r['paciente']}")
        await conn.close()
    except Exception as e:
        print(f"⚠️ Erro ao consultar banco: {e}")

def executar_fluxo():
    print("🚀 Iniciando teste do fluxo completo de ponta a ponta...")
    for i, texto in enumerate(passos_conversa, 1):
        payload = {
            "data": {
                "key": {"remoteJid": jid_teste, "fromMe": False},
                "message": {"conversation": texto}
            }
        }
        try:
            response = requests.post(URL, json=payload, timeout=10)
            if response.status_code == 200:
                data_resp = response.json()
                print(f"\n[Passo {i}] Paciente: '{texto}'")
                print(f"      -> Estado: {data_resp.get('estado_final')}")
                print(f"      -> Resposta Bot: {data_resp.get('resposta_enviada')}")
            else:
                print(f"\n[Passo {i}] ❌ Erro HTTP {response.status_code}: {response.text}")
        except Exception as e:
            print(f"\n[Passo {i}] ❌ Falha de Conexão: {e}")

if __name__ == "__main__":
    executar_fluxo()
    asyncio.run(verificar_banco())
