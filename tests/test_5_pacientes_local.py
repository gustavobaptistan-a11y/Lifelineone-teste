import requests
import time

URL = "http://127.0.0.1:8000/webhook"

# 5 personas simuladas com conversas completas e variadas (sem dependência de API externa)
fluxos_5_pacientes = [
    {
        "id": "pac_01",
        "nome": "Beatriz Lima",
        "mensagens": [
            "Olá, bom dia! Gostaria de agendar um atendimento.",
            "Beatriz Lima",
            "Dor lombar forte há 2 dias",
            "Particular",
            "Sim, primeira consulta",
            "Prefiro no período da tarde",
            "1"
        ]
    },
    {
        "id": "pac_02",
        "nome": "Carlos Eduardo",
        "mensagens": [
            "Oi, preciso de atendimento médico",
            "Carlos Eduardo Mendes",
            "Checkup de rotina",
            "Convênio Unimed",
            "Não, é retorno",
            "Período da manhã",
            "1"
        ]
    },
    {
        "id": "pac_03",
        "nome": "Fernanda Souza",
        "mensagens": [
            "Bom dia, quero marcar uma consulta",
            "Fernanda Souza",
            "Enxaqueca frequente",
            "Particular",
            "Sim, primeira vez",
            "Período da manhã",
            "1"
        ]
    },
    {
        "id": "pac_04",
        "nome": "Lucas Martins",
        "mensagens": [
            "Olá, preciso agendar médico",
            "Lucas Martins",
            "Exames de rotina",
            "Convênio Amil",
            "Não, é retorno",
            "Período da tarde",
            "1"
        ]
    },
    {
        "id": "pac_05",
        "nome": "Emergencia Teste",
        "mensagens": [
            "Socorro, estou sentindo uma dor no peito muito forte e falta de ar"
        ]
    }
]

def rodar_testes_locais():
    print("🚀 Iniciando testes simulados para 5 pacientes (Sem dependência de API externa)...\n")
    
    sucessos = 0
    erros = 0
    
    for idx, paciente in enumerate(fluxos_5_pacientes, 1):
        print(f"==================================================")
        print(f"👤 Paciente {idx}/5: {paciente['nome']}")
        print(f"==================================================")
        
        jid = f"5561997{paciente['id'][-2:]}@s.whatsapp.net"
        
        for turno, msg in enumerate(paciente['mensagens'], 1):
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
                    sucessos += 1
                    print(f"  [Turno {turno}] 👤 Usuário: '{msg}'")
                    print(f"           📍 Estado: {data.get('estado_final', 'N/A')}")
                    print(f"           🤖 Bot: {data.get('resposta_enviada', '')[:80]}...\n")
                else:
                    erros += 1
                    print(f"  [Turno {turno}] 🔴 Erro HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                erros += 1
                print(f"  [Turno {turno}] ❌ Falha de conexão: {e}")
            
            time.sleep(0.3)
        print("\n")

    print("==========================================")
    print(f"🏁 RESUMO DOS TESTES LOCAIS:")
    print(f"   - Turnos com Sucesso: {sucessos}")
    print(f"   - Falhas: {erros}")
    print("==========================================")

if __name__ == "__main__":
    rodar_testes_locais()
