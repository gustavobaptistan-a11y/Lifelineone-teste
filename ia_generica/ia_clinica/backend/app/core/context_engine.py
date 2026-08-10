import uuid
import datetime
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.clinic import Clinic
from app.models.patient import Patient, Contact, PatientContact
from app.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)


class ContextEngine:
    """
    Engine de Engenharia de Contexto Avançado.
    Responsável por sintetizar todo o estado relacional do paciente em um Prompt Clínico de Alta Precisão.
    - Perfil Dinâmico (Idade, Especialidade buscada, Familiaridade/Dependentes).
    - Memória de Longo Prazo (Consultas anteriores, faltas, preferências de horário).
    - Diretrizes de Tom Acolhedor & Empatia (Tratamento carinhoso pelo primeiro nome, escuta ativa).
    - Guardrails Clínicos & Segurança (Redirecionamento em emergências e limite prescritivo).
    """

    async def build_enriched_context_prompt(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        phone: str,
        patient_name: str,
        message_content: str,
        media_type: str = "texto",
        extracted_entities: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        entities = extracted_entities or {}

        # 1. Resgatar ou identificar contato e histórico no DB
        clean_phone = "".join(filter(str.isdigit, phone)) or phone
        stmt_contact = select(Contact).where(Contact.telefone.like(f"%{clean_phone[-8:]}%"))
        res_contact = await db.execute(stmt_contact)
        contact = res_contact.scalars().first()

        history_summary = []
        has_previous_bookings = False
        insurance_name = entities.get("insurance") or "Particular"

        if contact:
            stmt_pc = select(PatientContact).where(PatientContact.contact_id == contact.id)
            res_pc = await db.execute(stmt_pc)
            pc = res_pc.scalars().first()

            if pc:
                stmt_patient = select(Patient).where(Patient.id == pc.patient_id)
                res_patient = await db.execute(stmt_patient)
                patient = res_patient.scalars().first()

                if patient:
                    has_previous_bookings = True
                    if getattr(patient, "dados_clinicos_resumo", None):
                        history_summary.append(f"Histórico Clínico: {patient.dados_clinicos_resumo}")

            # Buscar mensagens anteriores para enriquecer o contexto
            stmt_conv = select(Conversation).where(Conversation.contact_id == contact.id).order_by(Conversation.started_at.desc())
            res_conv = await db.execute(stmt_conv)
            conv = res_conv.scalars().first()

            if conv:
                stmt_msgs = select(Message).where(Message.conversation_id == conv.id).order_by(Message.timestamp.desc()).limit(5)
                res_msgs = await db.execute(stmt_msgs)
                previous_messages = list(reversed(res_msgs.scalars().all()))
                for m in previous_messages:
                    sender = "Paciente" if m.sender_type == "paciente" else "IA Roberta"
                    history_summary.append(f"{sender}: {m.content}")

        # 2. Configurações da Clínica
        stmt_clinic = select(Clinic).where(Clinic.id == clinic_id)
        res_clinic = await db.execute(stmt_clinic)
        clinic = res_clinic.scalar_one_or_none()
        clinic_cfg = clinic.configuracoes if clinic and clinic.configuracoes else {}

        ai_name = clinic_cfg.get("nome_ia", "Roberta")
        clinic_name = clinic_cfg.get("nome_clinica", "Clínica de Alergia e Imunologia")

        # 3. Montar Prompt de Contexto Enriquecido
        formatted_history = "\n".join(history_summary) if history_summary else "Nenhum histórico prévio (Primeiro contato)."

        system_prompt = f"""
[DIRETRIZ MESTRA DE CONTEXTO E EMPATIA - IA {ai_name.upper()}]
Você é a {ai_name}, assistente virtual e recepcionista acolhedora da {clinic_name}.
Sua missão é cuidar do paciente com extrema empatia, carinho, escuta ativa e precisão cirúrgica.

[PERFIL DO PACIENTE EM ATENDIMENTO]
• Nome do Paciente: {patient_name}
• Telefone: {phone}
• Convênio / Plano: {insurance_name}
• Especialidade Requerida: {entities.get('specialty', 'Alergia e Imunologia')}
• Origem do Atendimento: {entities.get('campaign_origin', 'Direto')}
• Canal de Entrada: {media_type.upper()}

[HISTÓRICO E MEMÓRIA DE INTERAÇÕES ANTERIORES]
{formatted_history}

[REGRAS DE CONTEXTO E TOM DE VOZ ACOLHEDOR]
1. TRATAMENTO PERSONALIZADO: Use o primeiro nome do paciente ({patient_name.split()[0] if patient_name else 'Paciente'}) de forma calorosa.
2. ESCUTA EMPÁTICA: Quando o paciente relatar dor, crise alérgica, queda de cabelo ou preocupação com filhos, acolha primeiro antes de agendar. Exemplo: "Puxa, sinto muito por isso! Vamos cuidar de você com todo carinho."
3. CLAREZA OPERACIONAL: Forneça horários exatos (08:00, 09:00, 10:00, 14:00), endereço claro e valores quando solicitado.
4. SEGURANÇA MÉDICA E ÉTICA: A IA é 100% PROIBIDA de fornecer diagnósticos médicos, prescrever tratamentos ou citar hipóteses de doenças ao paciente. Explique sempre de forma empática que apenas o médico especialista pode realizar diagnósticos durante a consulta presencial, direcionando o paciente para o agendamento. Em emergências graves (falta de ar, reações anafiláticas), oriente ir ao pronto-socorro imediatamente.
""".strip()

        return {
            "ai_name": ai_name,
            "clinic_name": clinic_name,
            "patient_name": patient_name,
            "system_prompt": system_prompt,
            "formatted_history": formatted_history,
            "has_previous_bookings": has_previous_bookings,
            "entities": entities
        }


context_engine = ContextEngine()
