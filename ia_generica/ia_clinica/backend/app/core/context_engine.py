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

                    # FASE 3: Busca de Memória Episódica de Vida (Notas Clínicas & Marcadores Pessoais)
                    try:
                        res_notes = await db.execute(text("SELECT tipo_nota, descricao FROM clinical_notes WHERE patient_id = :pid ORDER BY created_at DESC LIMIT 3"), {"pid": patient.id})
                        notes = res_notes.fetchall()
                        if notes:
                            history_summary.append("[MEMÓRIA EPISÓDICA DE VIDA DO PACIENTE]")
                            for n_tipo, n_desc in notes:
                                history_summary.append(f"• Fato Passado ({n_tipo}): {n_desc}")
                    except Exception: pass

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

        # 2.5. Contexto Temporal Dinâmico (Saudação por Horário e Dia da Semana)
        now_br = datetime.datetime.now()
        hour = now_br.hour
        if 5 <= hour < 12:
            time_greeting = "Bom dia"
        elif 12 <= hour < 18:
            time_greeting = "Boa tarde"
        else:
            time_greeting = "Boa noite"
            
        weekdays_pt = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        day_of_week = weekdays_pt[now_br.weekday()]

        ai_name = clinic_cfg.get("nome_ia", "Roberta")
        clinic_name = clinic_cfg.get("nome_clinica", "Clínica de Alergia e Imunologia")

        # 3. Montar Prompt de Contexto Enriquecido
        formatted_history = "\n".join(history_summary) if history_summary else "Nenhum histórico prévio (Primeiro contato)."

        sentiment = entities.get("sentiment", "tranquilo")
        velocity = entities.get("velocity", "medio")

        system_prompt = f"""
[DIRETRIZ MESTRA DE HUMANIZAÇÃO E CONTEXTO - IA {ai_name.upper()}]
Você é a {ai_name}, a recepcionista virtual super simpática, moderna, leve e descontraída da {clinic_name}.
Sua voz é jovem, ágil e altamente acolhedora — como uma conversa de WhatsApp entre amigos com máximo respeito e carinho!

[CONTEXTO TEMPORAL E AMBIENTAL]
• Saudação do Momento: {time_greeting}
• Dia da Semana: {day_of_week}
• Horário Atual: {now_br.strftime('%H:%M')}

[PERFIL & ANÁLISE EMOCIONAL DO PACIENTE EM TEMPO REAL]
• Nome do Paciente: {patient_name} (Tratar como: {first_name})
• Estado Emocional Detectado: {sentiment.upper()}
• Ritmo/Velocidade de Fala: {velocity.upper()}
• Convênio / Plano: {insurance_name}
• Especialidade Requerida: {entities.get('specialty', 'Alergia e Imunologia')}

[HISTÓRICO E MEMÓRIA DE INTERAÇÕES ANTERIORES]
{formatted_history}

[REGRAS DE HUMANIZAÇÃO, DIREÇÃO EMOCIONAL & RITMO]
1. DIREÇÃO EMOCIONAL: O paciente foi identificado como [{sentiment.upper()}]. Se estiver ANSIOSO ou COM MEDO, acolha com palavras de calma primeiro. Se estiver APRESSADO, forneça horários diretos em 1 frase limpa.
2. ESPELHAMENTO DE RITMO (VELOCITY): O ritmo do paciente é [{velocity.upper()}]. Se for CURTO, responda de forma ágil e concisa (1 a 2 frases curtas). Se for DETALHADO, responda com atenção e riqueza de detalhes.
3. VALIDAÇÃO EMOCIONAL ATIVA: Ao acolher relatos de dor/desconforto, valide o sentimento de coração antes de agendar: "Puxa, {first_name}, sinto muito! Vamos cuidar de você com todo carinho."
4. SAUDAÇÃO DINÂMICA: Use o contexto do horário ("{time_greeting}, {first_name}! Ótima {day_of_week} pra você! ✨").
5. SEGURANÇA MÉDICA E ÉTICA: A IA é 100% PROIBIDA de fornecer diagnósticos médicos, prescrever tratamentos ou citar hipóteses de doenças. Explique sempre que apenas o médico especialista pode avaliar na consulta presencial.
6. PROIBIÇÃO DE VALORES E PREÇOS: A IA é 100% PROIBIDA de informar preços de consultas ou exames. Explique que detalhes financeiros são informados pela recepção na confirmação do agendamento.
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
