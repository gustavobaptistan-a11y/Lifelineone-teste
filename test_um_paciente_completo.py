import requests
import time

URL = "http://127.0.0.1:8000/webhook"

def testar_fluxo_um_paciente():
    print("🚀 Iniciando teste refinado de ponta a ponta para 1 paciente...\n")
    
    jid = "5561999997777@s.whatsapp.net"
    
    # Sequência correta e alinhada com as etapas do bot
    mensagens = [
        "Olá, boa tarde",                        # Turno 1 -> Inicia e pede Nome
        "Carlos Eduardo Mendes",                 # Turno 2 -> Coleta Nome e pede Sintoma
        "Dor nas costas intensa",                # Turno 3 -> Coleta Sintoma e pede Convênio
        "Particular",                            # Turno 4 -> Coleta Convênio e pede 1ª consulta
        "Sim, primeira vez",                     # Turno 5 -> Coleta 1ª consulta e pede Período
        "Período da tarde",                      # Turno 6 -> Coleta Período e exibe Horários
        "2"                                      # Turno 7 -> Confirma Opção 2 e Finaliza
    ]
    
    for turno, msg in enumerate(mensagens, 1):
        payload = {
            "data": {
                "key": {"remoteJid": jid, "fromMe": False},
                "message": {"conversation": msg}
            }
        }
        
        try:
            print(f"--------------------------------------------------")
            print(f"👉 [Turno {turno}] Mensagem enviada: '{msg}'")
            resp = requests.post(URL, json=payload, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"📌 Estado Alcançado: {data.get('estado_final')}")
                print(f"🤖 Resposta do Bot:\n{data.get('resposta_enviada')}\n")
            else:
                print(f"❌ Erro HTTP {resp.status_code}: {resp.text}")
                break
        except Exception as e:
            print(f"❌ Falha de conexão: {e}")
            break
            
        time.sleep(0.3)

if __name__ == "__main__":
    testar_fluxo_um_paciente()
