import requests
import time
import asyncio
import asyncpg
from app.config import settings

URL = "http://127.0.0.1:8000/webhook"

# Perfis de teste simulando fluxos completos e cenários de urgência
fluxos_pacientes = [
    {
        "id": "paciente_01",
        "nome": "Carlos Eduardo Mendes",
        "mensagens": [
            "Olá, quero marcar consulta",
            "Carlos Eduardo Mendes",
            "Dor nas costas frequente há dias",
            "Particular",
            "Sim, primeira consulta",
            "Prefiro no período da tarde",
            "1" # Escolhendo a primeira opção de horário
        ]
    },
    {
        "id": "paciente_02",
        "nome": "Mariana Costa Silva",
        "mensagens": [
            "Oi, preciso de atendimento médico",
            "Mariana Costa Silva",
            "Checkup de rotina",
            "Convênio Unimed",
            "Não, é retorno",
            "Período da manhã",
            "1"
        ]
    },
    {
        "id": "paciente_03",
        "nome": "Emergencia Teste",
        "mensagens": [
            "Socorro, estou sentindo uma dor no peito muito forte e falta de ar"
        ]
    }
]

async def verificar_banco_pos_teste():
    print("\n" + "="*50)
    print("📊 VERIFICAÇÃO DE PERSISTÊNCIA NO BANCO DE DADOS")
    print("="*50)
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        rows = await conn.fetch("SELECT id, status, paciente FROM agendamentos WHERE status = 'reservado';")
        if rows:
            print(f"✅ SUCESSO! Encontrado(s) {len(rows)} agendamento(s) reservado(s) no Supabase:")
            for r in rows:
                print(f"   - Slot ID: {r['id']} | Status: {r['status']} | Paciente: {r['paciente']}")
        else:
            print("⚠️ Nenhum agendamento com status 'reservado' encontrado no momento.")
        await conn.close()
    except Exception as e:
        print(f"❌ Erro ao conectar no PostgreSQL: {e}")

def rodar_testes_completos():
    print("🚀 Iniciando bateria de testes em massa (Fluxos Multi-turn + Banco)...\n")
    
    sucessos_totais = 0
    erros_totais = 0
    
    for paciente in fluxos_pacientes:
        print(f"--------------------------------------------------")
        print(f"👤 Simulando: {paciente['nome']}")
        print(f"--------------------------------------------------")
        
        jid = f"5561999{paciente['id'][-3:]}@s.whatsapp.net"
        
        for idx, msg in enumerate(paciente['mensagens'], 1):
            payload = {
                "data": {
                    "key": {"remoteJid": jid, "fromMe": False},
                    "message": {"conversation": msg}
                }
            }
            
            try:
                resp = requests.post(URL, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    sucessos_totais += 1
                    print(f"  [Turno {idx}] ' {msg} '")
                    print(f"         Estado: {data.get('estado_final', 'N/A')}")
                    print(f"         Bot: {data.get('resposta_enviada', '')[:80]}...\n")
                else:
                    erros_totais += 1
                    print(f"  [Turno {idx}] 🔴 Erro HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                erros_totais += 1
                print(f"  [Turno {idx}] ❌ Falha de conexão: {e}")
            
            time.sleep(0.3)
        print("\n")

    print(f"==========================================")
    print(f"🏁 RESUMO DOS TESTES:")
    print(f"   - Requisições com Sucesso: {sucessos_totais}")
    print(f"   - Falhas: {erros_totais}")
    print(f"==========================================")

if __name__ == "__main__":
    rodar_testes_completos()
    asyncio.run(verificar_banco_pos_teste())
