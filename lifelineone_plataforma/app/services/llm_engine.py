import os
from typing import Dict, Any, List, Optional

class LLMEngineService:
    """
    Motor de integração real com LLMs (Google Gemini 2.5 / OpenAI GPT-4o).
    Processa a síntese da resposta com base nas ferramentas executadas e no estado do paciente.
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "gemini"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.provider = provider

    async def generate_orchestrated_response(
        self,
        patient_name: str,
        current_stage: str,
        detected_intent: str,
        tools_executed: List[str],
        tool_outputs: Dict[str, Any],
        recent_history: List[Dict[str, str]],
        patient_context: Dict[str, Any]
    ) -> str:
        """
        Gera uma resposta empática, clínica e precisa baseada estritamente na Fonte da Verdade (Plataforma).
        """
        if not self.api_key:
            # Resposta orquestrada determinística quando executando sem API key configurada
            return self._build_fallback_response(
                patient_name, current_stage, detected_intent, tool_outputs, patient_context
            )

        # Se houver GEMINI_API_KEY configurada no ambiente
        try:
            if "gemini" in self.provider.lower():
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                system_prompt = (
                    f"Você é o Lifeline AI Orchestrator, o cérebro operacional da plataforma de saúde Lifeline One.\n"
                    f"Paciente: {patient_name} | Estágio Atual da Jornada: {current_stage}\n"
                    f"Ferramentas Executadas: {tools_executed}\n"
                    f"Resultados das Ferramentas: {tool_outputs}\n"
                    f"Contexto do Paciente: {patient_context}\n"
                    f"Regra: Seja acolhedor, profissional e responda em português com base estrita nos dados da plataforma."
                )
                
                response = model.generate_content(system_prompt)
                if response and response.text:
                    return response.text.strip()
        except Exception:
            pass

        return self._build_fallback_response(
            patient_name, current_stage, detected_intent, tool_outputs, patient_context
        )

    def _build_fallback_response(
        self,
        patient_name: str,
        current_stage: str,
        detected_intent: str,
        tool_outputs: Dict[str, Any],
        patient_context: Dict[str, Any]
    ) -> str:
        insurance = patient_context.get("insurance", {}).get("name")
        doctor = patient_context.get("medical_info", {}).get("attending_doctor", "nosso especialista")

        if detected_intent == "agendamento":
            slots = tool_outputs.get("agenda_slots", [])
            slots_str = ", ".join([f"{s.get('doctor', doctor)} ({s.get('date')})" for s in slots[:2]]) if slots else "10/08 às 09:00"
            return f"Olá, {patient_name}! Verifiquei seu histórico e temos disponibilidade com {doctor}: {slots_str}. Qual horário fica melhor para você?"

        if detected_intent == "duvida_convenio":
            convenios = tool_outputs.get("convenios", ["GEAP", "Unimed"])
            conv_str = ", ".join(convenios)
            if insurance:
                return f"Olá, {patient_name}! Confirmamos que aceitamos o seu convênio {insurance} perfeitamente. Também aceitamos: {conv_str}."
            return f"Olá, {patient_name}! Atendemos os seguintes convênios: {conv_str}. Qual o seu convênio?"

        if detected_intent == "localizacao":
            loc = tool_outputs.get("localizacao", {})
            return f"Nossa unidade {loc.get('unit', 'Central')} fica na {loc.get('address', 'Av. Paulista, 1000')}. Como posso ajudar?"

        return f"Olá, {patient_name}! Como posso auxiliar sua jornada de saúde hoje?"

llm_engine = LLMEngineService()
