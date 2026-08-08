from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient import Patient
from app.models.conversation import ConversationMessage, ConversationSummary
from app.schemas.patient import PatientCreate, PatientStateResponse
from app.services.patient_service import PatientService
from app.services.journey_service import JourneyService
from app.services.tools_service import PlatformToolsService

class LifelineAIOrchestrator:
    """
    O Cérebro Operacional da plataforma Lifeline One.
    Orquestra o raciocínio em 11 passos antes de gerar uma resposta ao paciente.
    """

    @staticmethod
    async def process_incoming_message(
        db: AsyncSession,
        phone: str,
        message_text: str,
        patient_name: Optional[str] = None
    ) -> Dict[str, Any]:
        
        # -------------------------------------------------------------
        # PASSO 1: Identificar o paciente (ou criar Lead se novo)
        # -------------------------------------------------------------
        patient = await PatientService.get_by_phone(db, phone)
        if not patient:
            patient = await PatientService.create_patient(
                db,
                PatientCreate(
                    name=patient_name or "Paciente sem nome",
                    phone=phone
                )
            )

        # Salva a mensagem recebida do paciente na memória
        user_msg = ConversationMessage(patient_id=patient.id, sender="paciente", content=message_text)
        db.add(user_msg)
        await db.flush()

        # -------------------------------------------------------------
        # PASSO 2: Buscar o estado atual da jornada
        # -------------------------------------------------------------
        patient_state: PatientStateResponse = await PatientService.get_patient_state(db, str(patient.id))

        # -------------------------------------------------------------
        # PASSO 3: Buscar contexto da conversa (Memória em 3 níveis)
        # -------------------------------------------------------------
        # Nível 1: Conversa Recente (últimas 10 mensagens)
        messages_query = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.patient_id == patient.id)
            .order_by(ConversationMessage.timestamp.desc())
            .limit(10)
        )
        recent_messages = list(reversed(messages_query.scalars().all()))

        # Nível 2: Resumo da Conversa
        summary_query = await db.execute(
            select(ConversationSummary)
            .where(ConversationSummary.patient_id == patient.id)
        )
        conversation_summary_obj = summary_query.scalar_one_or_none()
        conversation_summary = conversation_summary_obj.summary if conversation_summary_obj else "Sem resumo prévio."

        # Nível 3: Estado Persistente da Plataforma (Jaz em patient_state)

        # -------------------------------------------------------------
        # PASSO 4, 5 e 6: Informações clínicas, comerciais e eventos pendentes
        # -------------------------------------------------------------
        clinical_info = {
            "attending_doctor": patient_state.medical_info.attending_doctor,
            "specialty": patient_state.medical_info.specialty,
            "active_treatment": patient_state.active_treatment,
            "exams_data": patient_state.exams_data
        }
        commercial_info = {
            "insurance_name": patient_state.insurance.name,
            "insurance_plan": patient_state.insurance.plan
        }
        pending_events = {
            "pending_tasks": patient_state.pending_tasks,
            "expected_return": patient_state.expected_return_date
        }

        # -------------------------------------------------------------
        # PASSO 7: Entender a intenção atual
        # -------------------------------------------------------------
        msg_lower = message_text.lower()
        detected_intent = "duvida_geral"
        if any(w in msg_lower for w in ["agendar", "marcar", "horario", "consulta"]):
            detected_intent = "agendamento"
        elif any(w in msg_lower for w in ["convenio", "plano", "aceita"]):
            detected_intent = "duvida_convenio"
        elif any(w in msg_lower for w in ["onde", "endereco", "localizacao", "chegar"]):
            detected_intent = "localizacao"
        elif any(w in msg_lower for w in ["cancelar", "desmarcar"]):
            detected_intent = "cancelamento"

        # Atualiza a intenção atual no paciente
        patient.current_intent = detected_intent
        await db.flush()

        # -------------------------------------------------------------
        # PASSO 8 e 9: Decidir e executar ferramentas necessárias (Tools)
        # -------------------------------------------------------------
        tools_executed = []
        tool_outputs = {}

        if detected_intent == "agendamento":
            agenda_slots = await PlatformToolsService.consultar_agenda(
                db, doctor_name=patient_state.medical_info.attending_doctor, specialty=patient_state.medical_info.specialty
            )
            tools_executed.append("consultar_agenda")
            tool_outputs["agenda_slots"] = agenda_slots

        elif detected_intent == "duvida_convenio":
            convenios = await PlatformToolsService.consultar_convenios(db)
            tools_executed.append("consultar_convenios")
            tool_outputs["convenios"] = convenios

        elif detected_intent == "localizacao":
            loc = await PlatformToolsService.enviar_localizacao(db)
            tools_executed.append("enviar_localizacao")
            tool_outputs["localizacao"] = loc

        # -------------------------------------------------------------
        # PASSO 10: Atualizar a jornada (se aplicável)
        # -------------------------------------------------------------
        if detected_intent == "agendamento" and patient_state.current_stage == "lead_criado":
            await JourneyService.transition_stage(
                db=db,
                patient_id=patient.id,
                to_stage=patient_state.current_stage.PRE_QUALIFICACAO,
                trigger_event="intent_agendamento",
                notes="Paciente demonstrou intenção de agendamento"
            )

        # -------------------------------------------------------------
        # PASSO 11: Responder naturalmente com base no estado da jornada e ferramentas
        # -------------------------------------------------------------
        response_text = ""
        if detected_intent == "agendamento":
            slots_str = ", ".join([f"{s['doctor']} ({s['date']})" for s in tool_outputs.get("agenda_slots", [])[:2]])
            response_text = f"Olá, {patient.name}! Verifiquei sua jornada ({patient.current_stage.value}). Temos os seguintes horários disponíveis com {patient_state.medical_info.attending_doctor or 'nossa equipe'}: {slots_str}. Qual horário prefere?"
        elif detected_intent == "duvida_convenio":
            convenios_str = ", ".join(tool_outputs.get("convenios", []))
            conv_paciente = patient_state.insurance.name
            response_text = f"Olá, {patient.name}! Atendemos os seguintes convênios: {convenios_str}. " + (f"Confirmado que atendemos o seu convênio {conv_paciente}!" if conv_paciente else "Qual o seu convênio?")
        elif detected_intent == "localizacao":
            loc = tool_outputs.get("localizacao", {})
            response_text = f"Nossa unidade {loc.get('unit')} fica no endereço: {loc.get('address')}. Como posso te ajudar mais?"
        else:
            conv_info = f" (Convênio: {patient_state.insurance.name})" if patient_state.insurance.name else ""
            response_text = f"Olá, {patient.name}{conv_info}! Como posso ajudar você hoje?"

        # Salva a resposta da IA na memória
        ia_msg = ConversationMessage(patient_id=patient.id, sender="ia", content=response_text)
        db.add(ia_msg)
        await db.flush()

        return {
            "patient_id": patient.id,
            "current_stage": patient.current_stage.value,
            "detected_intent": detected_intent,
            "tools_executed": tools_executed,
            "tool_outputs": tool_outputs,
            "ai_response": response_text
        }
