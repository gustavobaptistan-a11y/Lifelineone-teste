def processar_fluxo_atendimento(estado_atual: str, texto_usuario: str, dados_sessao: dict) -> tuple:
    """
    Controla a transição estrita da máquina de estados e preenche o dicionário de dados da sessão.
    Retorna: (novo_estado, resposta_personalizada)
    """
    texto_limpo = texto_usuario.strip()
    
    if estado_atual == "inicio":
        return "coletar_nome", "Olá! Seja bem-vindo(a) à Clínica Lifeline. Para começarmos o seu atendimento, por favor, me informe o seu **nome completo**."
        
    elif estado_atual == "coletar_nome":
        dados_sessao["nome_paciente"] = texto_limpo
        return "coletar_sintoma", f"Obrigado, {texto_limpo}. Poderia descrever qual é o seu **sintoma principal** ou o motivo da consulta?"
        
    elif estado_atual == "coletar_sintoma":
        dados_sessao["sintoma"] = texto_limpo
        return "coletar_convenio", "Compreendo. O atendimento será na modalidade **Particular** ou por **Convênio**?"
        
    elif estado_atual == "coletar_convenio":
        dados_sessao["convenio"] = texto_limpo
        return "coletar_primeira_consulta", "Perfeito. É a sua **primeira consulta** com a nossa equipe ou trata-se de um **retorno**?"
        
    elif estado_atual == "coletar_primeira_consulta":
        dados_sessao["primeira_consulta"] = texto_limpo
        return "coletar_horario_preferencia", "Entendido. Qual **período do dia** você prefere para o atendimento? (Manhã ou Tarde)"
        
    elif estado_atual == "coletar_horario_preferencia":
        dados_sessao["preferencia_horario"] = texto_limpo
        horarios_disponiveis = (
            "📋 **Horários disponíveis:**\n"
            "1️⃣ Amanhã às 09:00\n"
            "2️⃣ Amanhã às 14:30\n"
            "3️⃣ Depois de amanhã às 10:00\n\n"
            "Por favor, digite o **número** da opção desejada para confirmar:"
        )
        return "aguardando_confirmacao_horario", horarios_disponiveis
        
    elif estado_atual == "aguardando_confirmacao_horario":
        dados_sessao["horario_escolhido"] = texto_limpo
        return "finalizado", "✅ **Consulta agendada com sucesso!** Enviamos os detalhes e orientações para você. Agradecemos a preferência e aguardamos a sua visita!"
        
    elif estado_atual == "finalizado":
        return "finalizado", "O seu atendimento anterior já foi concluído com sucesso. Caso queira iniciar um novo agendamento, digite 'olá'."
        
    else:
        return "inicio", "Olá! Vamos reiniciar o seu atendimento. Por favor, digite o seu nome completo."
