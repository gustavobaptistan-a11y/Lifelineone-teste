class LLMService:
    def __init__(self):
        pass

    def verificar_urgencia(self, texto_usuario: str) -> bool:
        """
        Verificação local simulada baseada em palavras-chave de urgência.
        """
        texto = texto_usuario.lower()
        palavras_urgentes = ["socorro", "emergência", "dor no peito", "falta de ar", "desmaio", "sangramento"]
        return any(p in texto for p in palavras_urgentes)

    def gerar_resposta_contextual(self, estado_atual: str, texto_usuario: str, historico: list = None) -> str:
        """
        Gera respostas imaginárias e contextuais baseadas puramente no estado atual.
        """
        respostas_mock = {
            "inicio": "Olá! Seja muito bem-vindo(a) à Clínica Lifeline. Para começarmos o seu atendimento, qual é o seu nome completo?",
            "coletar_name": f"Obrigado pelas informações. Poderia me descrever qual é o seu principal sintoma ou o motivo da sua consulta?",
            "coletar_sintoma": "Compreendo perfeitamente. O atendimento será na modalidade Particular ou por Convênio?",
            "coletar_convenio": "Perfeito. É a sua primeira consulta com o nosso especialista ou trata-se de um retorno?",
            "coletar_primeira_consulta": "Entendido. Qual período do dia você prefere para o atendimento? (Manhã ou Tarde)",
            "coletar_horario_preferencia": (
                "📋 **Horários disponíveis:**\n"
                "1️⃣ Amanhã às 09:00\n"
                "2️⃣ Amanhã às 14:30\n"
                "3️⃣ Depois de amanhã às 10:00\n\n"
                "Digite o número da opção desejada:"
            ),
            "finalizado": "✅ **Consulta agendada com sucesso!** Enviamos os detalhes para você. Esperamos sua visita!"
        }

        return respostas_mock.get(estado_atual, f"Recebido: '{texto_usuario}'. Vamos prosseguir para a próxima etapa.")

llm_service = LLMService()
