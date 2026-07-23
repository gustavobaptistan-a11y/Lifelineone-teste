import requests
import json
import time

URL = "http://127.0.0.1:8000/webhook"

def testar_integracao():
    print("🚀 Iniciando teste simulado do Webhook com a Evolution API...\n")
    
    # JID de teste simulando um número de WhatsApp real
    remote_jid = "5561988887777@s.whatsapp.net"
    
    # Sequência de mensagens simulando o chat do paciente
    mensagens_fluxo = [
        "Olá, boa tarde!",                    # Início -> Pede nome
        "Carlos Eduardo Teste",              # Nome -> Pede sintoma
        "Dor de cabeça forte e febre",       # Sintoma -> Pede convênio
        "Particular",                        # Convênio -> Pede primeira consulta
        "Sim, primeira vez",                 # Primeira consulta -> Pede período
        "Manhã",                             # Período -> Exibe opções de horários
        "1"                                  # Escolha de horário -> Finaliza e salva no banco
    ]
    
    for idx, msg in enumerate(mensagens_fluxo, 1):
        # Monta o payload exatamente no formato que a Evolution API envia para o webhook
        payload = {
            "event": "messages.upsert",
            "instance": "lifeline",
            "data": {
                "key": {
                    "remoteJid": remote_jid,
                    "fromMe": False,
                    "id": f"TEST_MSG_ID_{idx}"
                },
                "pushName": "Carlos Eduardo",
                "message": {
                    "conversation": msg
                },
                "messageType": "conversation"
            }
        }
        
        print(f"--------------------------------------------------")
        print(f"👉 [Passo {idx}] Enviando mensagem do usuário: '{msg}'")
        
        try:
            response = requests.post(URL, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook processado com sucesso!")
                print(f"📌 Estado Atual da Sessão: {data.get('estado_final')}")
                print(f"🤖 Resposta Gerada pelo Bot:\n{data.get('resposta_enviada')}\n")
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                break
        except Exception as e:
            print(f"❌ Falha ao conectar com o servidor local: {e}")
            break
            
        time.sleep(0.5) # Pequena pausa entre as mensagens

if __name__ == "__main__":
    testar_integracao()
