import re

PALAVRAS_CHAVE_URGENCIA = [
    "dor no peito",
    "falta de ar",
    "sangramento intenso",
    "desmaio",
    "perda de consciência",
    "convulsão",
    "dor muito forte",
    "pensamento suicida",
    "emergência"
]

def verificar_urgencia(texto: str) -> bool:
    texto_lower = texto.lower()
    for termo in PALAVRAS_CHAVE_URGENCIA:
        if termo in texto_lower:
            return True
    return False

def processar_fluxo_atendimento(estado_atual: str, texto_usuario: str, dados_sessao: dict) -> tuple:
    # 0. Interceptação crítica de urgência
    if verificar_urgencia(texto_usuario):
        resposta_emergencia = (
            "⚠️ **ATENÇÃO: Identificamos um possível caso de urgência médica.**\n\n"
            "Por favor, procure o pronto-socorro mais próximo ou ligue imediatamente para o **SAMU (192)**. "
            "Este canal automatizado não substitui o atendimento médico de emergência."
        )
        return resposta_emergencia, "urgencia_detectada", dados_sessao

    texto = texto_usuario.strip()
    proximo_estado = estado_atual

    # Máquina de Estados da Jornada do Paciente
    if estado_atual == "inicio":
        resposta = "Olá! Bem-vindo ao sistema de atendimento. Para começarmos, qual é o seu **nome completo**?"
        proximo_estado = "aguardando_nome"

    elif estado_atual == "aguardando_nome":
        dados_sessao["nome"] = texto
        resposta = f"Obrigado, {texto}. Qual é o principal **sintoma ou motivo** da sua consulta?"
        proximo_estado = "aguardando_sintoma"

    elif estado_atual == "aguardando_sintoma":
        dados_sessao["sintoma"] = texto
        resposta = "Qual é o seu **convênio médico** (ou se prefere atendimento particular)?"
        proximo_estado = "aguardando_convenio"

    elif estado_atual == "aguardando_convenio":
        dados_sessao["convenio"] = texto
        resposta = "Esta é a sua **primeira consulta** conosco? (Responda Sim ou Não)"
        proximo_estado = "aguardando_primeira_consulta"

    elif estado_atual == "aguardando_primeira_consulta":
        dados_sessao["primeira_consulta"] = texto
        resposta = "Perfeito. Temos horários disponíveis amanhã às **09:00** ou às **14:00**. Qual prefere?"
        proximo_estado = "aguardando_horario"

    elif estado_atual == "aguardando_horario":
        dados_sessao["horario"] = texto
        nome = dados_sessao.get("nome", "Paciente")
        convenio = dados_sessao.get("convenio", "Particular")
        horario = dados_sessao.get("horario", texto)
        resposta = (
            f"✅ **Consulta Agendada com Sucesso!**\n\n"
            f"Resumo:\n- Nome: {nome}\n- Convênio: {convenio}\n- Horário: {horario}\n\n"
            "Te aguardamos na clínica!"
        )
        proximo_estado = "concluido"

    else:
        resposta = "Seu atendimento já foi concluído. Caso precise de novo agendamento, digite 'olá'."
        proximo_estado = "inicio"

    return resposta, proximo_estado, dados_sessao
