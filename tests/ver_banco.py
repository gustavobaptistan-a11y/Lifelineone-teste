import json
import os

def inspecionar_banco():
    arquivo = "agendamentos_db.json"
    if not os.path.exists(arquivo):
        print("❌ Nenhum banco de dados encontrado ainda.")
        return

    with open(arquivo, "r", encoding="utf-8") as f:
        registros = json.load(f)

    print(f"📊 Total de agendamentos no banco estruturado: {len(registros)}\n")
    for idx, reg in enumerate(registros, 1):
        print(f"==================================================")
        print(f"📌 Registro #{idx} | ID: {reg.get('id_agendamento')}")
        print(f"   🕒 Data: {reg.get('data_criacao')} | Status: {reg.get('status_agendamento')}")
        print(f"   👤 Paciente: {reg.get('paciente', {}).get('nome_completo')} (WhatsApp: {reg.get('paciente', {}).get('contato')})")
        print(f"   🩺 Triagem:")
        print(f"      - Sintoma: {reg.get('triagem', {}).get('sintoma_principal')}")
        print(f"      - Convênio: {reg.get('triagem', {}).get('modalidade_atendimento')}")
        print(f"      - 1ª Consulta: {reg.get('triagem', {}).get('tipo_consulta')}")
        print(f"   📅 Horário:")
        print(f"      - Preferência: {reg.get('agendamento', {}).get('preferencia_periodo')}")
        print(f"      - Escolha: {reg.get('agendamento', {}).get('opcao_horario_escolhida')}")
    print(f"==================================================")

if __name__ == "__main__":
    inspecionar_banco()
