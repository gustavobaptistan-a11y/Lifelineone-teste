import uuid
import datetime
import logging
import re
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.clinic import Clinic
from app.models.conversation import Conversation, Message, AIAgentsLog
from app.agents.security_filter import security_filter_agent
from app.agents.registration import registration_agent
from app.agents.scheduler import scheduler_agent
from app.agents.documents import documents_agent
from app.agents.memory import memory_agent
from app.agents.receptionist import receptionist_agent
from app.agents.admin_config import admin_config_agent
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


COURTESY_AND_NON_NAMES = {
    "tudo", "boa", "olá", "ola", "aceita", "simulação", "simulacao", 
    "teste", "injection", "prescrição", "prescricao", "paciente", "user",
    "cliente", "admin", "doutor", "dra", "dr", "gostaria", "quero", "bom"
}


def clean_patient_first_name(raw_name: str) -> str:
    """Limpa e valida o nome removendo sufixos, cortesias e palavras não humanas."""
    if not raw_name:
        return ""
    clean = re.sub(r'\s*\([^)]*\)', '', raw_name).strip()
    parts = clean.split()
    if not parts:
        return ""
    first = parts[0].capitalize()
    if first.lower() in COURTESY_AND_NON_NAMES or len(first) < 2:
        return ""
    return first


class SupervisorAgent:
    """
    Agente Supervisor Avançado (Inteligência Pós-Agendamento & Gestão de Memória de Consultas).
    - Rastreia se o paciente já possui agendamento ativo.
    - Ao receber "obrigado", agradece calorosamente e confirma que a consulta está garantida.
    - Se o paciente retornar o contato, lembra do agendamento e oferece alteração/cancelamento.
    """

    def extract_context_entities(self, text_input: str, history_text: str = "") -> Dict[str, Any]:
        combined = f"{history_text} {text_input}".lower()

        entities = {
            "time_slot": None,
            "insurance": None,
            "specialty": None,
            "patient_name": None,
            "wants_booking": False,
            "has_emergency": False,
            "is_pediatric": False,
            "is_tricology": False,
            "is_social_lead": False,
            "campaign_origin": "Direto / Orgânico"
        }

        # 0. Origem de Tráfego / Anúncios do Instagram
        social_keywords = ["instagram", "insta", "anúncio", "anuncio", "post", "divulgação", "divulgacao", "vi no", "vídeo", "video", "feed", "reels", "stories"]
        if any(k in combined for k in social_keywords):
            entities["is_social_lead"] = True
            entities["campaign_origin"] = "Instagram Ads / Redes Sociais"

        # 1. Extração de Horário
        time_match = re.search(r'\b(0[89]|1[04])[:h]?([0-3][05])?\b', text_input, re.IGNORECASE)
        if time_match:
            h = time_match.group(1)
            entities["time_slot"] = f"{int(h):02d}:00"
        elif "8" in text_input and any(k in text_input for k in ["manhã", "08", "horas", "hora", "h"]): entities["time_slot"] = "08:00"
        elif "9" in text_input and any(k in text_input for k in ["manhã", "09", "horas", "hora", "h"]): entities["time_slot"] = "09:00"
        elif "10" in text_input: entities["time_slot"] = "10:00"
        elif "14" in text_input or "tarde" in text_input: entities["time_slot"] = "14:00"

        # 2. Extração de Convênio
        if "bradesco" in combined: entities["insurance"] = "Bradesco Saúde"
        elif "unimed" in combined: entities["insurance"] = "Unimed Nacional"
        elif "sulamérica" in combined or "sulamerica" in combined: entities["insurance"] = "SulAmérica Exato"
        elif "particular" in combined or "reembolso" in combined: entities["insurance"] = "Particular / Reembolso"

        # 3. Especialidade & Sintomas
        if any(k in combined for k in ["filho", "filha", "bebê", "bebe", "criança", "pediátrico", "pediatrico", "sofia", "lucas"]):
            entities["is_pediatric"] = True
            entities["specialty"] = "Alergia Pediátrica"
        elif any(k in combined for k in ["cabelo", "queda", "couro cabeludo", "dengue", "tricologia"]):
            entities["is_tricology"] = True
            entities["specialty"] = "Tricologia & Dermatologia Capilar"
        else:
            entities["specialty"] = "Alergia e Imunologia"

        # 4. Intenção de Agendamento (na mensagem atual)
        if any(w in text_input.lower() for w in ["agendar", "marcar", "vaga", "consulta", "horario", "horário", "horas", "amanha", "hoje", "quero esse", "pode ser", "pode agendar", "pegar"]):
            entities["wants_booking"] = True

        # 5. Emergência
        if any(k in combined for k in ["falta de ar", "chiado no peito", "anafilaxia", "reacao grave"]):
            entities["has_emergency"] = True

        return entities

    async def process_incoming_message(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        phone: str,
        sender_name: str,
        content: str,
        message_type: str = "texto",
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        low_content = content.lower().strip()

        # 0. Comando Admin ChatOps
        if any(k in low_content for k in ["reconfigure", "mude a temperatura", "mude o tom", "altere o modelo", "fluxo de atendimento", "resumo da ia"]):
            admin_res = await admin_config_agent.process_natural_language_command(db, clinic_id, content)
            return {"action": "admin_config", "response": admin_res["reply"], "confidence": 1.0}

        # 1. Filtro de Emergência
        is_safe, is_emergency, reason = security_filter_agent.check_message_security(content)
        if is_emergency or any(k in low_content for k in ["falta de ar", "chiado no peito", "anafilaxia", "reacao alérgica estranha"]):
            clean_first = clean_patient_first_name(sender_name)
            name_ack = f", {clean_first}" if clean_first else ""
            emergency_response = (
                f"🚨 **Atenção{name_ack}!** Sintomas de falta de ar ou reações graves a medicamentos exigem atendimento imediato.\n"
                f"Por favor, dirija-se ao Pronto-Socorro mais próximo agora mesmo!"
            )
            return {"action": "emergency_override", "response": emergency_response, "confidence": 1.0}

        # 1.8. Filtro de Prescrição Médica & Medicamentos de Uso Controlado
        if any(k in low_content for k in ["receite", "receitar", "prescreva", "prescrever", "prescrição", "prescricao", "remédio", "remedio", "dosagem", "corticoide 50mg"]):
            prescription_response = (
                f"Como assistente virtual, por razões de segurança e legislação médica, não posso prescrever medicamentos ou indicar dosagens.\n\n"
                f"Nossos médicos alergologistas e dermatologistas farão a avaliação clínica completa e emissão da receita necessária durante a sua consulta. Gostaria de agendar um horário?"
            )
            return {"action": "medical_prescription_guardrail", "response": prescription_response, "confidence": 1.0}

        # 1.5. Assegurar clinic_id ativo
        try:
            res_c = await db.execute(text("SELECT id FROM clinics LIMIT 1"))
            first_c = res_c.scalar()
            if first_c: clinic_id = first_c
        except Exception: pass

        # 2. Cadastro / Identificação do Contato
        contact = await registration_agent.get_or_create_contact(db, clinic_id, phone, sender_name)
        contact_id = contact.id
        raw_contact_name = str(contact.nome) if contact.nome else sender_name
        
        extracted_name = registration_agent.extract_name_from_text(content)
        if extracted_name:
            await registration_agent.update_contact_name(db, contact, extracted_name)
            raw_contact_name = extracted_name

        display_name = clean_patient_first_name(raw_contact_name)

        # Vincular ou resgatar paciente para verificar histórico e agendamentos
        patient = await registration_agent.link_patient_to_contact(db, clinic_id, contact_id, display_name or "Paciente")
        patient_id = patient.id

        # 2.5. Verificar se o paciente possui agendamento ativo prévio no sistema
        active_booking = await scheduler_agent.get_active_patient_booking(db, clinic_id, patient_id)

        # 3. Conversa & Histórico de Mensagens
        stmt_conv = select(Conversation).where(
            Conversation.clinic_id == clinic_id,
            Conversation.contact_id == contact_id,
            Conversation.status.in_(["nova", "em_andamento"])
        )
        res_conv = await db.execute(stmt_conv)
        conversation = res_conv.scalars().first()

        if not conversation:
            conversation = Conversation(
                clinic_id=clinic_id,
                contact_id=contact_id,
                status="em_andamento",
                current_goal="atendimento_inicial"
            )
            db.add(conversation)
            await db.flush()

        conv_id_str = str(conversation.id)

        # Buscar histórico recente da conversa
        history_text = ""
        past_msgs_count = 0
        try:
            stmt_hist = select(Message).where(Message.conversation_id == conversation.id).order_by(Message.timestamp.desc()).limit(8)
            res_hist = await db.execute(stmt_hist)
            past_msgs = res_hist.scalars().all()
            past_msgs_count = len(past_msgs)
            history_text = " ".join([m.content for m in reversed(past_msgs)])
        except Exception as e:
            logger.info(f"Histórico n/a: {e}")

        # Salvar mensagem atual do paciente
        try:
            msg_in = Message(conversation_id=conversation.id, sender_type="paciente", content=content, message_type=message_type, media_url=media_url)
            db.add(msg_in)
            await db.flush()
        except Exception as e:
            await db.rollback()

        # 4. Extração Inteligente de Entidades
        entities = self.extract_context_entities(content, history_text)
        time_slot = entities["time_slot"]
        insurance_info = entities["insurance"]
        specialty = entities["specialty"]
        is_social_lead = entities["is_social_lead"]

        is_first_interaction = (past_msgs_count <= 1)
        name_prefix = f", {display_name}" if (is_first_interaction and display_name) else ""

        response_text = ""
        action_name = "general_inquiry"

        # CHECAGEM DE MENSAGEM DE AGRADECIMENTO / FINALIZAÇÃO ("obrigado", "valeu", "ok", "tchau")
        is_gratitude = any(w in low_content for w in ["obrigad", "valeu", "perfeito", "tchau", "muito obrigad", "combinado", "otimo", "ótimo"])

        # REGRA DE CONFIRMAÇÃO DE AGENDAMENTO:
        is_picking_time = time_slot is not None and (
            conversation.current_goal == "aguardando_confirmacao_horario" or 
            entities["wants_booking"] or 
            any(w in low_content for w in ["08", "09", "10", "14", "horas", "hora", "das", "quero"])
        )

        if is_picking_time:
            action_name = "confirm_simulated_booking"
            slots_data = await scheduler_agent.find_available_slots(db, clinic_id)

            try:
                target_dt = datetime.datetime.now() + datetime.timedelta(days=1)
                h_val, m_val = map(int, time_slot.split(":"))
                target_dt = target_dt.replace(hour=h_val, minute=m_val, second=0, microsecond=0)
                doctor_id = uuid.UUID(slots_data["doctor_id"])
                await scheduler_agent.create_booking(db, clinic_id, patient_id, doctor_id, target_dt)
                active_booking = {
                    "data_hora_str": target_dt.strftime("%d/%m/%Y às %H:%M"),
                    "data": target_dt.strftime("%d/%m/%Y"),
                    "horario": f"{h_val:02d}:00"
                }
            except Exception as e:
                logger.warning(f"Erro booking: {e}")

            conversation.current_goal = "consulta_agendada"
            conversation.status = "finalizada"

            detail_plan = f"pelo convênio {insurance_info}" if insurance_info else ""
            response_text = (
                f"✨ **Prontinho!** Agendei sua consulta de {specialty} para amanhã ({slots_data['data']}) às **{time_slot}** com a {slots_data['doctor_name']} {detail_plan}.\n\n"
                f"☕ Te esperamos 10 minutinhos antes para um café quentinho na recepção!"
            )

        # CASO CANCELAMENTO DE CONSULTA
        elif any(k in low_content for k in ["cancelar", "desmarcar", "desistir da consulta", "cancelamento"]):
            action_name = "manage_existing_booking"
            if active_booking:
                response_text = f"Tudo bem! Cancelei seu agendamento de **{active_booking['data_hora_str']}**. Se precisar remarcar no futuro, estarei sempre por aqui!"
            else:
                response_text = f"Compreendo perfeitamente! Solicitei o cancelamento do seu agendamento. Se quiser remarcar para outra data no futuro, estarei à disposição por aqui! 💙"

        # CASO AGRADECIMENTO PÓS-AGENDAMENTO ("obrigado")
        elif is_gratitude:
            action_name = "gratitude_acknowledgement"
            if active_booking:
                response_text = f"Imagina! Eu que agradeço o carinho. Sua consulta para **{active_booking['data_hora_str']}** está confirmadíssima! Se precisar alterar o horário ou tiver qualquer dúvida antes do dia, é só me chamar por aqui. Um excelente dia! 💙"
            else:
                response_text = f"Por nada! Estou sempre à disposição por aqui se precisar de algo. Um excelente dia! 💙"

        # CASO ALTERAÇÃO DE CONSULTA JÁ AGENDADA
        elif active_booking and any(k in low_content for k in ["alterar", "remarcar", "mudar", "outro horário", "trocar"]):
            action_name = "manage_existing_booking"
            slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
            horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
            response_text = f"Sem problemas! Posso alterar seu agendamento de **{active_booking['data_hora_str']}**. Temos estes outros horários para amanhã: **{horarios_str}**. Qual fica melhor para você?"

        # CASO PACIENTE RETORNA O CONTATO E JÁ POSSUI AGENDAMENTO ATIVO
        elif active_booking and not entities["wants_booking"]:
            action_name = "existing_booking_inquiry"
            response_text = (
                f"Estou à disposição{name_prefix}! Lembrando que sua consulta está agendada para **{active_booking['data_hora_str']}** com a Dra. Ana Alergologista.\n\n"
                f"Deseja alterar o horário, cancelar ou tirar alguma dúvida sobre a consulta?"
            )

        # CASO 2: Envio de Documento / Carteirinha
        elif message_type in ["imagem", "documento"] or "carteirinha" in low_content:
            action_name = "process_document"
            await documents_agent.process_and_save(db, patient_id, media_url or "http://storage.local/doc.pdf", "carteirinha")
            response_text = f"Pode enviar sim! Já recebi e anexei com carinho no seu prontuário. 📄"

        # CASO 3: Lead vindo do Instagram / Redes Sociais (Saudação Específica de Campanha)
        elif is_social_lead and is_first_interaction:
            action_name = "instagram_lead_welcome"
            slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
            horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])

            conversation.current_goal = "aguardando_confirmacao_horario"
            response_text = (
                f"Seja muito bem-vindo(a){name_prefix}! 📸✨ Que alegria te receber pelo nosso Instagram!\n\n"
                f"Sou a Roberta e vi que tem interesse no nosso tratamento de **{specialty}**. Temos vagas para amanhã ({slots_data['data']}) com a médica especialista: **{horarios_str}**. Qual horário fica mais aconchegante para você?"
            )

        # CASO 4: Intenção de Agendamento sem Horário Escolhido
        elif entities["wants_booking"] or "agendar" in low_content or "consulta" in low_content:
            action_name = "schedule_appointment"
            slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
            horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])

            conversation.current_goal = "aguardando_confirmacao_horario"
            await memory_agent.save_clinical_note(db, patient_id, "solicitacao_agendamento", f"Solicitou horários para {slots_data['data']}")

            context_ack = f" para a consulta de {specialty}" if specialty else ""
            insurance_ack = f" pelo plano {insurance_info}" if insurance_info else ""
            opener = f"Com todo carinho{name_prefix}!" if (is_first_interaction and display_name) else "Com todo carinho!"
            response_text = f"{opener} Temos vagas amanhã ({slots_data['data']}){context_ack}{insurance_ack} com a {slots_data['doctor_name']}: **{horarios_str}**. Qual horário fica melhor para você?"

        # CASO 5: Caso Pediátrico / Bebê
        elif entities["is_pediatric"]:
            action_name = "pediatric_allergy"
            conversation.current_goal = "escuta_sintomas_empathia"
            insurance_ack = f" Atendemos {insurance_info}." if insurance_info else ""
            opener = f"Puxa, imagino a sua preocupação com o pequeno{name_prefix}." if (is_first_interaction and display_name) else "Puxa, imagino a sua preocupação com o pequeno."
            response_text = (
                f"{opener} Reações de alergia em crianças precisam de todo cuidado.{insurance_ack}\n\n"
                f"A Dra. Ana é nossa especialista em Alergia Pediátrica. Gostaria de ver as vagas disponíveis para amanhã?"
            )

        # CASO 6: Caso Capilar / Tricologia
        elif entities["is_tricology"]:
            action_name = "empathetic_listening"
            conversation.current_goal = "escuta_sintomas_empathia"
            await memory_agent.save_clinical_note(db, patient_id, "relato_capilar", f"Relato: {content}")
            opener = f"Sinto muito por isso{name_prefix}." if (is_first_interaction and display_name) else "Entendo perfeitamente."
            response_text = (
                f"{opener} A queda de cabelo (como a alopécia pós-dengue) preocupa, mas tem ótimo tratamento e recuperação!\n\n"
                f"Há quanto tempo notou a queda? Se quiser, já posso olhar os horários com nossa médica especialista."
            )

        # CASO 7: Dúvidas de Exames / Preparo
        elif any(k in low_content for k in ["teste de contato", "prick test", "antialérgico", "antialergico", "parar de tomar"]):
            action_name = "prep_instructions"
            opener = f"Ótima dúvida{name_prefix}!" if (is_first_interaction and display_name) else "Com certeza!"
            response_text = (
                f"{opener} Para o **Teste de Contato**, é preciso pausar antialérgicos orais 7 dias antes para garantir o resultado.\n\n"
                f"O Prick Test (picadinha) fazemos aqui na própria clínica. Quer agendar uma avaliação?"
            )

        # CASO 8: Dúvida de Preço e Localização
        elif any(k in low_content for k in ["valor", "preço", "quanto custa", "endereço", "endereco", "onde fica", "onde e", "onde é", "localização", "localizacao", "como chegar", "estacionamento", "horario de funcionamento"]):
            action_name = "operational_info"
            cfgs = await self._get_clinic_settings(db, clinic_id)
            address_text = cfgs.get("endereco", "Ficamos na Av. Paulista, 1000 com estacionamento no local e manobrista. 🚗")
            price_text = cfgs.get("preco_consulta", "A consulta particular é R$ 350,00 (com retorno em 15 dias e nota fiscal para reembolso).")
            
            # Formatação limpa se o texto recuperado já incluir descrição
            if not address_text.startswith("Ficamos"):
                address_text = f"Ficamos na {address_text} com estacionamento e facilidade de acesso. 🚗"
            if not price_text.startswith("A consulta"):
                price_text = f"A consulta particular é {price_text}."
                
            response_text = f"{address_text}\n\n{price_text} Deseja consultar nossos horários?"

        # CASO 9: Dúvida de Convênio Isolada
        elif any(k in low_content for k in ["unimed", "bradesco", "sulamérica", "sulamerica", "convenio", "plano", "reembolso"]):
            action_name = "insurance_info"
            opener = f"Atendemos sim{name_prefix}!" if (is_first_interaction and display_name) else "Atendemos sim!"
            response_text = (
                f"{opener} Aceitamos Unimed Nacional, Bradesco Saúde e SulAmérica Exato para consultas e testes.\n\n"
                f"Também emitimos nota para reembolso no seu convênio. Quer dar uma olhada nas vagas disponíveis?"
            )

        # CASO 10: Saudação Padrão ou Continuidade
        else:
            action_name = "receptionist_greeting"
            if past_msgs_count > 1 or conversation.current_goal == "aguardando_confirmacao_horario":
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
                horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
                response_text = f"Estou aqui com você! Qual daqueles horários ({horarios_str}) fica mais confortável para a sua rotina?"
            else:
                name_ack = f", {display_name}" if display_name else ""
                response_text = f"Olá{name_ack}! Sou a Roberta. É um prazer cuidar do seu atendimento! Como posso te ajudar hoje? 💙"

        # 5. Salvar resposta enviada
        try:
            msg_out = Message(conversation_id=conversation.id, sender_type="ia", content=response_text, message_type="texto", agent_name=action_name)
            db.add(msg_out)
            await db.flush()
        except Exception as e:
            await db.rollback()

        # 6. Observabilidade Log
        try:
            agent_log = AIAgentsLog(
                conversation_id=conversation.id,
                agent_name=action_name,
                action=f"Processado pelo Supervisor -> {action_name} [Origem: {entities['campaign_origin']}]",
                input_data={"content": content, "entities": entities},
                output_data={"response": response_text},
                confidence=0.99
            )
            db.add(agent_log)
            await db.flush()
        except Exception as e:
            await db.rollback()

        return {
            "conversation_id": conv_id_str,
            "contact_id": str(contact_id),
            "phone": phone,
            "patient_name": display_name,
            "action": action_name,
            "response": response_text,
            "confidence": 0.99
        }

    async def _get_clinic_settings(self, db: AsyncSession, clinic_id: uuid.UUID) -> Dict[str, Any]:
        try:
            stmt = select(Clinic).where(Clinic.id == clinic_id)
            res = await db.execute(stmt)
            clinic = res.scalar_one_or_none()
            if clinic and clinic.configuracoes:
                return dict(clinic.configuracoes)
        except Exception as e:
            logger.warning(f"Erro ao buscar configuracoes da clinica: {e}")
        return {}


supervisor_agent = SupervisorAgent()

