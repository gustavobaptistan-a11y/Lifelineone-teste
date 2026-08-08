class ReceptionistAgent:
    """
    Agente Recepcionista.
    Garante o tom humanizado, empático, acolhedor e profissional em todas as respostas.
    """

    def format_welcoming_response(self, text: str, patient_name: str = "Paciente") -> str:
        name_str = patient_name if patient_name and patient_name != "Paciente" else "você"
        if not text.startswith("Olá") and not text.startswith("Seja") and not text.startswith("✨") and not text.startswith("Entendo"):
            text = f"Olá, {name_str}! {text}"
        return text


receptionist_agent = ReceptionistAgent()
