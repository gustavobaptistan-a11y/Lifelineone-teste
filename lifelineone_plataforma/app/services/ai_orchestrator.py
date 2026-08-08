import unicodedata
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient import Patient
from app.models.conversation import ConversationMessage, ConversationSummary
from app.models.ticket import SupportTicket, TicketStatus
from app.schemas.patient import PatientCreate, PatientStateResponse
from app.services.patient_service import PatientService
from app.services.journey_service import JourneyService
from app.services.tools_service import PlatformToolsService
from app.services.llm_engine import llm_engine
from app.core.websocket_manager import ws_manager

def normalize_text(text: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

class LifelineAIOrchestrator:
    """
    O Cérebro Operacional da plataforma Lifeline One.
    Orquestra o raciocínio em 11 passos e suporta transbordo para atendimento humano.
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

        # Checa se há atendimento humano ativo (Transbordo Humano)
        if patient.active_ticket_id:
            ticket_res = await db.execute(
                select(SupportTicket).where(SupportTicket.id == int(patient.active_ticket_id))
            )
            active_ticket = ticket_res.scalar_one_or_none()
            if active_ticket and active_ticket.status == TicketStatus.ASSUMIDO_HUMANO:
                # Transmite a mensagem recebida ao vivo para a tela do atendente
                await ws_manager.broadcast({
                    "type": "human_message_received",
                    "ticket_id": active_ticket.id,
                    "patient_id": patient.id,
                    "patient_name": patient.name,
                    "message": message_text,
                    "assigned_agent": active_ticket.assigned_agent
                })
                return {
                    "patient_id": patient.id,
                    "current_stage": patient.current_stage.value,
                    "detected_intent": "transbordo_humano",
                    "tools_executed": [],
                    "tool_outputs": {},
                    "ai_response": f"[Atendimento Humano Assumido por {active_ticket.assigned_agent}] Mensagem encaminhada ao painel."
                }

        # -------------------------------------------------------------
        # PASSO 2: Buscar o estado atual da jornada
        # -------------------------------------------------------------
        patient_state: PatientStateResponse = await PatientService.get_patient_state(db, str(patient.id))

        # -------------------------------------------------------------
        # PASSO 3: Buscar contexto da conversa (Memória em 3 níveis)
        # -------------------------------------------------------------
        messages_query = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.patient_id == patient.id)
            .order_by(ConversationMessage.timestamp.desc())
            .limit(10)
        )
        recent_messages = list(reversed(messages_query.scalars().all()))

        summary_query = await db.execute(
            select(ConversationSummary)
            .where(ConversationSummary.patient_id == patient.id)
        )
        conversation_summary_obj = summary_query.scalar_one_or_none()
        conversation_summary = conversation_summary_obj.summary if conversation_summary_obj else "Sem resumo prévio."

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

        # -------------------------------------------------------------
        # PASSO 7: Entender a intenção atual
        # -------------------------------------------------------------
        msg_normalized = normalize_text(message_text)
        detected_intent = "duvida_geral"
        if any(w in msg_normalized for w in ["agendar", "marcar", "horario", "consulta"]):
            detected_intent = "agendamento"
        elif any(w in msg_normalized for w in ["convenio", "plano", "aceita"]):
            detected_intent = "duvida_convenio"
        elif any(w in msg_normalized for w in ["onde", "endereco", "localizacao", "local", "chegar"]):
            detected_intent = "localizacao"
        elif any(w in msg_normalized for w in ["cancelar", "desmarcar"]):
            detected_intent = "cancelamento"

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
        # PASSO 11: Responder naturalmente via Motor LLM / Plataforma
        # -------------------------------------------------------------
        history_list = [{"sender": m.sender, "text": m.content} for m in recent_messages]
        
        response_text = await llm_engine.generate_orchestrated_response(
            patient_name=patient.name,
            current_stage=patient.current_stage.value,
            detected_intent=detected_intent,
            tools_executed=tools_executed,
            tool_outputs=tool_outputs,
            recent_history=history_list,
            patient_context={
                "insurance": commercial_info,
                "medical_info": clinical_info,
                "summary": conversation_summary
            }
        )

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
