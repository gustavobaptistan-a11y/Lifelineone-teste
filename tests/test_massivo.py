import requests
import time

URL = "http://127.0.0.1:8000/webhook"

casos_teste = [
    {"id": "paciente_01", "nome": "Carlos Silva", "msg": "Olá, gostaria de marcar uma consulta"},
    {"id": "paciente_01", "nome": "Carlos Silva", "msg": "Meu nome é Carlos Alberto da Silva"},
    {"id": "paciente_02", "nome": "Ana Souza", "msg": "Oi, preciso agendar um atendimento"},
    {"id": "paciente_02", "nome": "Ana Souza", "msg": "Ana Clara Souza"},
    {"id": "paciente_03", "nome": "Marcos Lima", "msg": "Boa tarde, quero marcar consulta"},
    {"id": "paciente_03", "nome": "Marcos Lima", "msg": "Marcos Vinicius Lima"},
    {"id": "paciente_04", "nome": "Juliana Costa", "msg": "Olá quero agendar medico"},
    {"id": "paciente_04", "nome": "Juliana Costa", "msg": "Juliana Mendes Costa"},
    {"id": "paciente_05", "nome": "Roberto Dias", "msg": "Bom dia, preciso de atendimento"},
    {"id": "paciente_05", "nome": "Roberto Dias", "msg": "Roberto Carlos Dias"},
    {"id": "paciente_06", "nome": "Fernanda Lima", "msg": "Olá gostaria de marcar consulta"},
    {"id": "paciente_06", "nome": "Fernanda Lima", "msg": "Fernanda Souza Lima"},
    {"id": "paciente_07", "nome": "Lucas Martins", "msg": "Oi, preciso marcar um horário"},
    {"id": "paciente_07", "nome": "Lucas Martins", "msg": "Lucas Gabriel Martins"},
    {"id": "paciente_08", "nome": "Patrícia Rocha", "msg": "Boa tarde, quero agendar"},
    {"id": "paciente_08", "nome": "Patrícia Rocha", "msg": "Patrícia Alves Rocha"},
    {"id": "paciente_09", "nome": "Urgencia 1", "msg": "Estou sentindo uma dor no peito muito forte"},
    {"id": "paciente_10", "nome": "Urgencia 2", "msg": "Estou com falta de ar severa e tontura"},
    {"id": "paciente_11", "nome": "Urgencia 3", "msg": "Aconteceu um desmaio aqui em casa"},
    {"id": "paciente_12", "nome": "Urgencia 4", "msg": "Estou tendo um sangramento intenso"},
    {"id": "paciente_13", "nome": "Urgencia 5", "msg": "A pessoa teve uma convulsao agora"},
    {"id": "paciente_14", "nome": "Urgencia 6", "msg": "Dor muito forte na cabeça, acho que é avc"},
    {"id": "paciente_15", "nome": "Desatento 1", "msg": "Quero marcar consulta"},
    {"id": "paciente_15", "nome": "Desatento 1", "msg": "Estou com dor de cabeça há 3 dias"},
    {"id": "paciente_16", "nome": "Desatento 2", "msg": "Olá bom dia"},
    {"id": "paciente_16", "nome": "Desatento 2", "msg": "Sou convênio Unimed"},
    {"id": "paciente_17", "nome": "Curto 1", "msg": "Marcar"},
    {"id": "paciente_17", "nome": "Curto 1", "msg": "Bruno"},
    {"id": "paciente_18", "nome": "Curto 2", "msg": "Consulta por favor"},
    {"id": "paciente_18", "nome": "Curto 2", "msg": "Camila"},
    {"id": "paciente_19", "nome": "Detalhado", "msg": "Olá, sou o Paulo e quero marcar cardiologista particular urgente"},
    {"id": "paciente_20", "nome": "Variacao", "msg": "Boa tarde equipe LifelineOne, preciso de atendimento"}
]

def executar_testes_massa():
    print(f"🚀 Iniciando bateria de testes simulando os fluxos de atendimento...\n")
    sucessos = 0
    erros = 0

    for idx, caso in enumerate(casos_teste, 1):
        payload = {
            "data": {
                "key": {
                    "remoteJid": f"55619999{caso['id'][-2:]}@s.whatsapp.net",
                    "fromMe": False
                },
                "message": {
                    "conversation": caso["msg"]
                }
            }
        }

        try:
            response = requests.post(URL, json=payload, timeout=10)
            if response.status_code == 200:
                data_resp = response.json()
                print(f"[{idx}/{len(casos_teste)}] 🟢 {caso['id']} ({caso['nome']}): '{caso['msg']}'")
                print(      f"      -> Resposta Bot: {data_resp.get('resposta_enviada', 'OK')[:80]}...")
                sucessos += 1
            else:
                print(f"[{idx}/{len(casos_teste)}] 🔴 {caso['id']} - Erro HTTP {response.status_code}: {response.text}")
                erros += 1
        except Exception as e:
            print(f"[{idx}/{len(casos_teste)}] ❌ {caso['id']} - Falha de Conexão: {e}")
            erros += 1

        time.sleep(0.1)

    print(f"\n==========================================")
    print(f"📊 RELATÓRIO DE TESTES CONCLUÍDO:")
    print(f"   - Total testado: {len(casos_teste)}")
    print(f"   - Sucessos (HTTP 200): {sucessos}")
    print(f"   - Erros: {erros}")
    print(f"==========================================")

if __name__ == "__main__":
    executar_testes_massa()
