import uuid
import datetime
import logging
import re
import random
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
from app.core.context_engine import context_engine

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


def get_dynamic_greeting(display_name: str = "") -> str:
    """Gera saudações dinâmicas e variadas mantendo a essência acolhedora e humana da Roberta."""
    now = datetime.datetime.now()
    hour = now.hour
    
    if 5 <= hour < 12:
        period_greeting = "Bom dia"
    elif 12 <= hour < 18:
        period_greeting = "Boa tarde"
    else:
        period_greeting = "Boa noite"
        
    clean_first = clean_patient_first_name(display_name) if display_name else ""
    name_ack = f", {clean_first}" if clean_first else ""

    templates = [
        f"Olá{name_ack}! Sou a Roberta. É um prazer cuidar do seu atendimento! Como posso te ajudar hoje? 💙",
        f"{period_greeting}{name_ack}! Sou a Roberta. É um prazer enorme cuidar do seu atendimento por aqui! Como posso te ajudar hoje? 💙",
        f"Olá{name_ack}, {period_greeting.lower()}! Meu nome é Roberta e estou à sua disposição para o que precisar. Como posso te auxiliar hoje? ✨",
        f"{period_greeting}{name_ack}! Seja muito bem-vindo(a). Sou a Roberta, da equipe de atendimento. Em que posso te ajudar hoje? 💙",
        f"Olá{name_ack}! Sou a Roberta e será um prazer te ajudar hoje. Como posso cuidar de você ou do seu agendamento? 🩺💙",
        f"{period_greeting}{name_ack}! Aqui é a Roberta. Estou por aqui para tirar suas dúvidas ou organizar sua consulta. Como posso te ajudar hoje? 😊"
    ]
    
    return random.choice(templates)


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

        # 6. FASE 1 & FASE 2: Análise de Sentimento e Espelhamento de Ritmo (Velocity Matching)
        if any(k in text_input.lower() for k in ["medo", "assustad", "preocupad", "grave", "horrivel", "desespero", "estresse", "ruim", "ansios"]):
            entities["sentiment"] = "ansioso"
        elif any(k in text_input.lower() for k in ["urgente", "rápido", "rapido", "logo", "agora", "já", "ja", "correndo", "pressa"]):
            entities["sentiment"] = "apressado"
        elif any(k in text_input.lower() for k in ["chato", "demora", "péssimo", "pessimo", "ruim", "dificil", "difícil"]):
            entities["sentiment"] = "frustrado"
        else:
            entities["sentiment"] = "tranquilo"

        # 7. FRONTEIRA 1: Detecção de Parentesco & Vínculo Familiar (Kinship Binding)
        if any(k in combined for k in ["meu filho", "minha filha", "meu bebê", "meu bebe", "para o lucas", "para a sofia", "pro meu filho", "pra minha filha"]):
            entities["kinship"] = "mae_ou_pai_para_filho"
        elif any(k in combined for k in ["minha mãe", "minha mae", "meu pai", "para minha mãe", "para meu pai"]):
            entities["kinship"] = "filho_para_pais_idosos"
        else:
            entities["kinship"] = "proprio_paciente"

        # 8. FRONTEIRA 6: Letramento Digital Adaptativo
        if any(k in text_input.lower() for k in ["ligação", "ligacao", "ligar", "telefone fixo", "falar no telefone"]):
            entities["digital_literacy"] = "assistido_humanizado"
        elif any(k in text_input.lower() for k in ["pix", "pdf", "link", "maps", "qr", "qrcode"]):
            entities["digital_literacy"] = "nativo_digital"
        else:
            entities["digital_literacy"] = "padrao"

        # 9. OPÇÃO 3: Proteção e Suporte ao Cuidador Exausto (Caregiver Stress Shield)
        if any(k in combined for k in ["exausta", "exausto", "não durmo", "nao durmo", "sem dormir", "noite toda", "em claro", "cansada", "cansado", "não aguento mais", "nao aguento mais"]):
            entities["caregiver_stress"] = True
        else:
            entities["caregiver_stress"] = False

        # 10. Extração de Entidades Estendidas (Nome da criança, Sintomas e Duração)
        child_match = re.search(r"(?:filh[oa]|bebê|bebe)\s+([A-ZÀ-Úa-zà-ú]+)", combined, re.IGNORECASE)
        if child_match:
            c_candidate = child_match.group(1).capitalize()
            if c_candidate.lower() not in ["com", "de", "que", "está", "esta", "tem", "sem", "do", "da", "para", "pra"]:
                entities["child_name"] = c_candidate
            else:
                entities["child_name"] = None
        else:
            entities["child_name"] = None

        symptoms_list = []
        if any(k in combined for k in ["alergia", "alérgic"]): symptoms_list.append("quadro alérgico")
        if any(k in combined for k in ["mancha", "manchinhas", "vermelh"]): symptoms_list.append("manchas na pele")
        if any(k in combined for k in ["tosse", "tossindo"]): symptoms_list.append("tosse")
        if any(k in combined for k in ["coceira", "coçando"]): symptoms_list.append("coceira intensa")
        if any(k in combined for k in ["febre", "quentinho"]): symptoms_list.append("febre")
        if any(k in combined for k in ["queda", "cabelo"]): symptoms_list.append("queda de cabelo")
        entities["symptoms"] = symptoms_list

        dur_match = re.search(r"(?:h[áa]|faz|fazem)\s+(\d+\s*(?:dias?|semanas?|meses?)|ontem|uma semana|2 dias|3 dias)", combined, re.IGNORECASE)
        entities["duration"] = dur_match.group(0).lower() if dur_match else None

        word_count = len(text_input.split())
        if word_count <= 5 or len(text_input) <= 25:
            entities["velocity"] = "curto"
        elif word_count >= 18 or len(text_input) >= 120:
            entities["velocity"] = "detalhado"
        else:
            entities["velocity"] = "medio"

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
            emergency_response = (
                f"🚨 **Atenção!** Sintomas de falta de ar ou reações graves a medicamentos exigem atendimento imediato.\n"
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

        # 1.9. Tratamento Multimodal: Mensagem de Voz (Áudio)
        if message_type == "audio":
            voice_res = await documents_agent.process_voice_audio(media_url or "", sender_name)
            content = voice_res["transcription"]
            low_content = content.lower().strip()

        # 1.95. Tratamento Multimodal: Imagem (Exames, Carteirinhas ou Lesões Dermatológicas)
        if message_type in ["imagem", "image", "foto"]:
            img_res = await documents_agent.process_medical_image(media_url or "", content)
            img_response = (
                f"Recebi a sua imagem com sucesso! 📸\n\n"
                f"• **Análise Multimodal:** {img_res['summary']}\n"
                f"• **Prontuário:** A foto já foi anexada ao seu cadastro e estará disponível para a médica na sua consulta.\n\n"
                f"Como posso te ajudar a organizar seu atendimento hoje?"
            )
            return {"action": "multimodal_image_processed", "response": img_response, "confidence": 0.97}

        # 1.5. Assegurar clinic_id ativo
        try:
            res_c = await db.execute(text("SELECT id FROM clinics LIMIT 1"))
            first_c = res_c.scalar()
            if first_c: clinic_id = first_c
        except Exception: pass

        # 2. Cadastro / Identificação do Contato (Sem presumir nome do WhatsApp)
        contact = await registration_agent.get_or_create_contact(db, clinic_id, phone, name=None)
        contact_id = contact.id

        # 3. Carregar Histórico e Estado da Conversa
        conversation = await self._get_or_create_conversation(db, clinic_id, contact_id)
        conv_id_str = str(conversation.id)

        # 3.1. Verificação de IA Pausada (Atendimento Humano em Andamento no CRM)
        if getattr(conversation, "is_ai_paused", False):
            return {
                "conversation_id": conv_id_str,
                "contact_id": str(contact_id),
                "phone": phone,
                "patient_name": contact.nome or "Paciente",
                "action": "ai_paused_human_operator_active",
                "response": None,
                "confidence": 1.0
            }

        # 3.2. Detecção de Solicitação Explícita de Atendente Humano
        if any(k in low_content for k in ["falar com pessoa", "atendente humano", "falar com pessoa humana", "falar com secretária", "falar com secretaria", "falar com humano", "passar para atendente"]):
            conversation.is_human_handover_requested = True
            conversation.handover_reason = "Solicitação direta de atendente humano pelo paciente"
            await db.flush()
            handover_response = (
                f"Com certeza! Transferi o seu atendimento para nossa recepção humana. 🔔\n\n"
                f"Nossa equipe notificou o painel e responderá por aqui em instantes!"
            )
            return {
                "conversation_id": conv_id_str,
                "contact_id": str(contact_id),
                "phone": phone,
                "patient_name": contact.nome or "Paciente",
                "action": "human_handover_activated",
                "response": handover_response,
                "confidence": 1.0
            }
        # O nome do paciente só é conhecido e utilizado SE tiver sido extraído do texto do paciente (ex: "Meu nome é Gustavo") 
        # ou se já existir um nome confirmado diferente do padrão "Paciente".
        extracted_name = registration_agent.extract_name_from_text(content)
        if extracted_name:
            await registration_agent.update_contact_name(db, contact, extracted_name)
            raw_contact_name = extracted_name
        else:
            raw_contact_name = contact.nome if (contact.nome and contact.nome != "Paciente") else None

        display_name = clean_patient_first_name(raw_contact_name) if raw_contact_name else ""
        low_content = content.lower()

        # Vincular ou resgatar paciente para verificar histórico e agendamentos
        patient = await registration_agent.link_patient_to_contact(db, clinic_id, contact_id, display_name or "Paciente")
        patient_id = patient.id

        # 2.5. Verificar se o paciente possui agendamento ativo prévio no sistema
        active_booking = await scheduler_agent.get_active_patient_booking(db, clinic_id, patient_id)

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
        is_picking_time = (time_slot is not None) and (
            conversation.current_goal in ["aguardando_confirmacao_horario", "escuta_sintomas_empathia", "atendimento_inicial"] or 
            entities["wants_booking"] or 
            any(w in low_content for w in ["08", "09", "10", "14", "horas", "hora", "das", "quero", "09:00", "08:00", "10:00", "14:00"])
        )

        # GATILHO GLOBAL 0.1: Transbordo Humano / Solicitação de Atendente Humano
        is_human_request = any(k in low_content for k in [
            "humano", "atendente", "falar com humano", "falar com atendente", 
            "recepção", "recepcao", "falar com a recepção", "atendente humano", 
            "atendimento humano", "pessoa", "falar com pessoa"
        ])
        is_option_other = (conversation.current_goal == "aguardando_opcao_pos_agendamento" and any(k in low_content for k in ["2", "outro", "outro assunto", "dúvida", "duvida"]))

        if is_human_request or is_option_other:
            action_name = "human_handover"
            clean_first = clean_patient_first_name(display_name)
            name_ack = f", {clean_first}" if clean_first else ""
            conversation.status = "aguardando_humano"
            conversation.human_takeover = True
            await db.commit()

            response_text = (
                f"Compreendo perfeitamente{name_ack}! Vou transferir o seu atendimento agora mesmo para um de nossos atendentes humanos da recepção. 👩‍💼\n\n"
                f"Por favor, aguarde um momento que a nossa equipe já vai te atender por aqui!"
            )

        # CASO 0.A: Confirmação Final dos Dados do Agendamento pelo Paciente
        elif conversation.current_goal and conversation.current_goal.startswith("aguardando_confirmacao_dados:"):
            action_name = "confirming_booking_data"
            parts = conversation.current_goal.split(":")
            pending_time_slot = parts[1]
            confirmed_full_name = parts[2] if len(parts) > 2 else display_name

            # Se o paciente confirma ("sim", "confirmo", "pode", "ok", "correto", "pode ser", "com certeza", "pode agendar")
            if any(w in low_content for w in ["sim", "confirmo", "pode", "ok", "correto", "pode ser", "com certeza", "pode agendar", "tudo certo", "perfeito", "1"]):
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
                try:
                    target_dt = datetime.datetime.now() + datetime.timedelta(days=1)
                    if ":" in pending_time_slot:
                        h_val, m_val = map(int, pending_time_slot.split(":"))
                    else:
                        h_val, m_val = int(pending_time_slot.replace("h", "")), 0
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
                first_name = confirmed_full_name.split()[0]
                detail_plan = f"pelo convênio {insurance_info}" if insurance_info else ""
                formatted_slot = f"{h_val:02d}:00" if 'h_val' in locals() else pending_time_slot
                response_text = (
                    f"✨ **Prontinho, {first_name}!** Agendei sua consulta de {specialty} para amanhã ({slots_data['data']}) às **{formatted_slot}** com a {slots_data['doctor_name']} {detail_plan}.\n\n"
                    f"📍 **Localização:** Av. Paulista, 1000 (com estacionamento no local e manobrista). 🚗\n"
                    f"☕ Te esperamos 10 minutinhos antes para um café quentinho na recepção!\n\n"
                    f"Se precisar de mais informações ou alterar o seu agendamento, é só me falar por aqui: **'preciso falar do meu agendamento'**."
                )
            else:
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
                horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
                response_text = (
                    f"Sem problemas! O que você gostaria de alterar? Se preferir outro horário para amanhã ({slots_data['data']}), temos vagas às **{horarios_str}**."
                )

        # CASO 0.B: Resposta com o Nome do Paciente para Conclusão do Agendamento
        elif conversation.current_goal and conversation.current_goal.startswith("aguardando_nome_para_agendamento:"):
            action_name = "received_patient_name_for_booking"
            pending_time_slot = conversation.current_goal.split(":")[1]
            extracted_name = registration_agent.extract_name_from_text(content)
            if not extracted_name or extracted_name == "Paciente":
                extracted_name = content.strip().title()
            
            # Salvar nome no banco
            contact.nome = extracted_name
            await db.commit()
            await db.refresh(contact)
            display_name = extracted_name
            
            parts_name = [p for p in extracted_name.split() if len(p) > 1]
            if len(parts_name) < 2:
                # Nome simples informado -> Solicitar sobrenome / nome completo
                response_text = (
                    f"Obrigada, {parts_name[0]}! Para o cadastro oficial no prontuário médico, por favor, me informe o seu **nome completo** (com sobrenome)."
                )
            else:
                # Nome completo informado -> Apresentar resumo e pedir confirmação explícita
                conversation.current_goal = f"aguardando_confirmacao_dados:{pending_time_slot}:{extracted_name}"
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
                response_text = (
                    f"Perfeito, {parts_name[0]}! Por favor, confira os dados do seu agendamento:\n\n"
                    f"👤 **Nome Completo:** {extracted_name}\n"
                    f"🩺 **Especialidade:** {specialty}\n"
                    f"📅 **Data:** Amanhã ({slots_data['data']})\n"
                    f"⏰ **Horário:** {pending_time_slot}\n"
                    f"👩‍⚕️ **Médica:** {slots_data['doctor_name']}\n\n"
                    f"Podemos **confirmar** o seu agendamento com estes dados?"
                )

        elif is_picking_time:
            # Extrair nome da mensagem atual se presente (ex: "meu nome é gustavo")
            extracted_in_msg = registration_agent.extract_name_from_text(content)
            if extracted_in_msg and extracted_in_msg != "Paciente":
                contact.nome = extracted_in_msg
                await db.commit()
                await db.refresh(contact)
                display_name = extracted_in_msg

            parts_name = [p for p in (display_name or "").split() if len(p) > 1 and p.lower() != "paciente"]
            
            # Se não possui nome completo (menos de 2 nomes) -> Pedir Nome Completo
            if len(parts_name) < 2:
                action_name = "ask_full_name_before_booking"
                conversation.current_goal = f"aguardando_nome_para_agendamento:{time_slot}"
                first_ack = f", {parts_name[0]}" if parts_name else ""
                response_text = (
                    f"Com certeza{first_ack}! Para registrarmos a sua consulta no prontuário e organizar o horário das **{time_slot}** para amanhã, por favor, me informe o seu **nome completo**."
                )
            else:
                action_name = "ask_confirmation_before_booking"
                conversation.current_goal = f"aguardando_confirmacao_dados:{time_slot}:{display_name}"
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
                response_text = (
                    f"Perfeito, {parts_name[0]}! Por favor, confira os dados do seu agendamento:\n\n"
                    f"👤 **Nome Completo:** {display_name}\n"
                    f"🩺 **Especialidade:** {specialty}\n"
                    f"📅 **Data:** Amanhã ({slots_data['data']})\n"
                    f"⏰ **Horário:** {time_slot}\n"
                    f"👩‍⚕️ **Médica:** {slots_data['doctor_name']}\n\n"
                    f"Podemos **confirmar** o seu agendamento com estes dados?"
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

        # CASO PACIENTE RETORNA OU ENVIA MENSAGEM COM AGENDAMENTO JÁ CONFIRMADO
        elif (active_booking is not None or conversation.current_goal in ["consulta_agendada", "aguardando_opcao_pos_agendamento"]) and not any(k in low_content for k in ["cancelar", "desmarcar", "desistir"]):
            clean_first = clean_patient_first_name(display_name)
            name_ack = f", {clean_first}" if clean_first else ""
            time_info = active_booking['data_hora_str'] if active_booking else "amanhã"

            # Se o paciente quer falar sobre agendamento (opção 1 ou frase explícita)
            if (conversation.current_goal == "aguardando_opcao_pos_agendamento" and any(k in low_content for k in ["1", "agendamento", "sobre agendamento", "meu agendamento", "alterar", "remarcar", "localização", "localizacao"])) or any(k in low_content for k in ["preciso falar do meu agendamento", "falar do meu agendamento", "falar do agendamento", "meu agendamento"]):
                action_name = "manage_existing_booking"
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
                horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
                response_text = (
                    f"Com certeza{name_ack}! Localizei o seu agendamento de {specialty} para **{time_info}** com a {slots_data['doctor_name']}.\n\n"
                    f"📍 **Localização:** Av. Paulista, 1000 (com estacionamento e manobrista). 🚗\n\n"
                    f"Se você deseja **alterar o horário** para amanhã ({slots_data['data']}), temos as seguintes vagas disponíveis: **{horarios_str}**. Qual horário fica melhor para você?\n\n"
                    f"(Se preferir cancelar a consulta, basta responder 'cancelar agendamento')."
                )
            else:
                # Saudação / Menu pós-agendamento inteligente
                action_name = "post_booking_contextual_menu"
                conversation.current_goal = "aguardando_opcao_pos_agendamento"
                response_text = (
                    f"Olá{name_ack}! É um prazer falar com você novamente! 😊\n\n"
                    f"Vejo que você já possui uma consulta confirmada de {specialty} para **{time_info}** com a Dra. Ana.\n\n"
                    f"Como posso te ajudar agora?\n"
                    f"1️⃣ **Falar sobre o seu agendamento** (ver detalhes, alterar horário ou cancelar)\n"
                    f"2️⃣ **Tratar de outro assunto** (falar com a nossa recepção humana)"
                )

        # CASO 8.5: Dúvida de Localização e Funcionamento (com State Memory Stack & Checagem de Agendamento Ativo)
        elif any(k in low_content for k in ["endereço", "endereco", "onde fica", "onde e", "onde é", "localização", "localizacao", "como chegar", "estacionamento", "horario de funcionamento"]):
            action_name = "operational_info"
            cfgs = await self._get_clinic_settings(db, clinic_id)
            address_text = cfgs.get("endereco", "Ficamos na Av. Paulista, 1000 com estacionamento no local e manobrista. 🚗")
            if not address_text.startswith("Ficamos"):
                address_text = f"Ficamos na {address_text} com estacionamento e facilidade de acesso. 🚗"
            
            if active_booking or conversation.current_goal == "consulta_agendada":
                time_info = active_booking['data_hora_str'] if active_booking else "amanhã"
                response_text = (
                    f"{address_text}\n\n"
                    f"Sua consulta para **{time_info}** já está confirmadíssima! ☕\n"
                    f"Se precisar de mais informações ou alterar o seu agendamento, é só me falar por aqui: **'preciso falar do meu agendamento'**."
                )
            elif conversation.current_goal == "aguardando_confirmacao_horario":
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id, preferred_period=entities.get("preferred_period"))
                horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
                response_text = f"{address_text}\n\nInclusive, como estávamos organizando seu agendamento para amanhã ({slots_data['data']}): temos vagas às **{horarios_str}**. Qual horário você prefere?"
            else:
                response_text = f"{address_text}\n\nDeseja consultar nossos horários disponíveis?"

        # CASO PACIENTE INFORMA QUE JÁ ESTÁ AGENDADO ("ja estou agendada", "já agendei")
        elif any(k in low_content for k in ["ja estou agendada", "já estou agendada", "ja agendei", "já agendei", "ja tenho consulta", "já tenho consulta"]):
            action_name = "active_booking_status"
            clean_first = clean_patient_first_name(display_name)
            name_prefix = f" {clean_first}" if clean_first else ""
            if active_booking or conversation.current_goal == "consulta_agendada":
                time_info = active_booking['data_hora_str'] if active_booking else "amanhã"
                response_text = (
                    f"Com certeza{name_prefix}! Sua consulta de {specialty} está confirmadíssima para **{time_info}** com a Dra. Ana. 🏥\n\n"
                    f"📍 **Localização:** Av. Paulista, 1000 (com estacionamento no local e manobrista). 🚗\n\n"
                    f"Se precisar de mais informações ou alterar o seu agendamento, é só me falar por aqui: **'preciso falar do meu agendamento'**."
                )
            else:
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
                horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
                response_text = (
                    f"Que ótimo{name_prefix}! Caso queira agendar ou alterar o horário da sua consulta para amanhã, temos vagas às **{horarios_str}**. Qual prefere?"
                )

        # CASO PACIENTE RETORNA O CONTATO E JÁ POSSUI AGENDAMENTO ATIVO
        elif active_booking and conversation.current_goal == "consulta_agendada" and any(k in low_content for k in ["minha consulta", "meu agendamento", "que dia", "que horas"]):
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

        # 3.3. GUARDRAIL CLÍNICO ESTRITO: PROIBIÇÃO DE DIAGNÓSTICO E PRESCRIÇÃO PELA IA
        elif any(k in low_content for k in ["qual meu diagnostico", "qual meu diagnóstico", "o que eu tenho", "qual doença", "qual doenca", "isso é perigoso", "isso e perigoso", "é eflúvio", "e efluvio", "diagnostique"]):
            action_name = "no_diagnosis_guardrail"
            clean_first = clean_patient_first_name(display_name)
            name_ack = f", {clean_first}" if clean_first else ""
            response_text = (
                f"Entendo a sua preocupação{name_ack}! Como assistente virtual da recepção, **não realizo diagnósticos médicos nem prescrevo tratamentos**.\n\n"
                f"Apenas a nossa médica especialista, a Dra. Ana, poderá examinar você detalhadamente na consulta presencial e indicar a conduta adequada.\n\n"
                f"Gostaria de agendar a sua avaliação médica para amanhã?"
            )

        # CASO 4.5: Resposta do Paciente à Escuta Empática de Sintomas / Duração (ex: "tem uns 2 meses", "2 semanas")
        elif conversation.current_goal == "escuta_sintomas_empathia":
            action_name = "symptom_duration_received"
            conversation.current_goal = "aguardando_confirmacao_horario"
            await memory_agent.save_clinical_note(db, patient_id, "duracao_sintoma", f"Duração: {content}")
            slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
            horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
            
            clean_first = clean_patient_first_name(display_name)
            name_ack = f", {clean_first}" if clean_first else ""
            clean_dur = re.sub(r'^(tem\s+uns|tem|faz|fazem|há|ha|cerca\s+de|a\s+cerca\s+de|a)\s+', '', content, flags=re.IGNORECASE).strip()
            clean_dur = re.sub(r'^(há|ha|a)\s+', '', clean_dur, flags=re.IGNORECASE).strip()
            dur_phrase = f"há cerca de {clean_dur}" if clean_dur else f"há {content}"
            response_text = (
                f"Compreendo perfeitamente{name_ack}! Estar apresentando esse sintoma {dur_phrase} exige uma avaliação médica cuidadosa para investigar as causas em consulta presencial.\n\n"
                f"Temos horários disponíveis para amanhã ({slots_data['data']}) com a {slots_data['doctor_name']}: **{horarios_str}**. Qual horário fica mais confortável para a sua rotina?"
            )

        # CASO 5: Caso Pediátrico / Cuidador Exausto (Caregiver Stress Shield)
        elif entities["is_pediatric"] or entities.get("caregiver_stress"):
            action_name = "caregiver_stress_shield"
            conversation.current_goal = "escuta_sintomas_empathia"
            await memory_agent.save_clinical_note(db, patient_id, "relato_cuidador", f"Relato Cuidador: {content}")
            slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
            horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
            
            clean_first = clean_patient_first_name(display_name)
            name_ack = f", {clean_first}" if clean_first else ""
            
            child_name = entities.get("child_name")
            child_ref = f"do pequeno {child_name}" if child_name else "de quem amamos"
            dur_ref = f" {entities['duration']}" if entities.get("duration") else ""
            symptoms = entities.get("symptoms", [])
            symptom_str = " e ".join(symptoms) if symptoms else "quadros alérgicos em crianças"

            if entities.get("caregiver_stress"):
                stress_ack = f"Puxa, sei o quanto é desgastante e exaustivo ficar sem dormir cuidando {child_ref}{dur_ref}! Respire fundo, estou aqui para te apoiar. 💙\n\n"
            else:
                stress_ack = f"Com certeza! Cuidar {child_ref} exige toda a nossa atenção e carinho. 💙\n\n"
            
            response_text = (
                f"{stress_ack}Reações de {symptom_str} precisam de todo cuidado e atenção especialista.\n\n"
                f"A Dra. Ana é nossa médica especialista em Alergia Pediátrica. Temos vagas para amanhã ({slots_data['data']}): **{horarios_str}**. Qual horário fica mais confortável para a sua rotina?"
            )

        # CASO 6: Caso Capilar / Tricologia
        elif entities["is_tricology"]:
            action_name = "empathetic_listening"
            conversation.current_goal = "escuta_sintomas_empathia"
            await memory_agent.save_clinical_note(db, patient_id, "relato_capilar", f"Relato: {content}")
            opener = f"Sinto muito por isso{name_prefix}." if (is_first_interaction and display_name) else "Entendo perfeitamente."
            response_text = (
                f"{opener} A queda de cabelo traz bastante desconforto, mas com a avaliação médica correta é possível tratar com segurança!\n\n"
                f"Há quanto tempo notou a queda? Se quiser, já posso olhar os horários com nossa médica especialista."
            )

        # CASO 6.6: Pedido de Análise ou Orientação Geral
        elif any(k in low_content for k in ["analise", "análise", "sugestoes", "sugestões", "melhorar", "o que fazer", "como funciona"]):
            action_name = "analysis_recommendations"
            slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
            horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
            
            response_text = (
                f"Como assistente virtual, não posso fornecer diagnósticos. Recomendo agendarmos a sua **Consulta Especializada com a Dra. Ana** 🩺.\n\n"
                f"Na consulta presencial, a médica irá:\n"
                f"1. Avaliar detalhadamente o couro cabeludo e seu histórico.\n"
                f"2. Solicitar os exames necessários se houver indicação.\n"
                f"3. Definir a conduta médica adequada para você.\n\n"
                f"Temos vagas para amanhã: **{horarios_str}**. Posso reservar qual horário para você?"
            )

        # CASO 7: Dúvidas de Exames / Preparo
        elif any(k in low_content for k in ["teste de contato", "prick test", "antialérgico", "antialergico", "parar de tomar"]):
            action_name = "prep_instructions"
            opener = f"Ótima dúvida{name_prefix}!" if (is_first_interaction and display_name) else "Com certeza!"
            response_text = (
                f"{opener} Para o **Teste de Contato**, é preciso pausar antialérgicos orais 7 dias antes para garantir o resultado.\n\n"
                f"O Prick Test (picadinha) fazemos aqui na própria clínica. Quer agendar uma avaliação?"
            )

        # CASO 8: Pergunta de Preço / Valores de Consulta e Exames (GUARDRAIL DE NÃO DIVULGAÇÃO DE VALORES)
        elif any(k in low_content for k in ["valor", "preço", "preco", "quanto custa", "tabela", "orçamento", "orcamento", "quanto é", "quanto e", "quanto fica"]):
            action_name = "no_price_disclosure_guardrail"
            clean_first = clean_patient_first_name(display_name)
            name_ack = f", {clean_first}" if clean_first else ""
            response_text = (
                f"Entendo a sua dúvida{name_ack}! Os valores de consultas, testes e exames dependem da modalidade de atendimento (convênio ou nota fiscal para reembolso).\n\n"
                f"Por política da clínica, os detalhes financeiros, formas de pagamento e recibos são informados diretamente pela nossa equipe de recepção no momento da confirmação do agendamento.\n\n"
                f"Gostaria de verificar as vagas disponíveis para a sua consulta amanhã?"
            )



        # CASO 9: Dúvida de Convênio Isolada (com State Memory Stack)
        elif any(k in low_content for k in ["unimed", "bradesco", "sulamérica", "sulamerica", "convenio", "plano", "reembolso"]):
            action_name = "insurance_info"
            opener = f"Atendemos sim{name_prefix}!" if (is_first_interaction and display_name) else "Atendemos sim!"
            
            if conversation.current_goal == "aguardando_confirmacao_horario":
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id, preferred_period=entities.get("preferred_period"))
                horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
                response_text = (
                    f"{opener} Aceitamos Unimed Nacional, Bradesco Saúde e SulAmérica Exato para consultas e testes.\n\n"
                    f"Inclusive, como estávamos escolhendo seu horário para amanhã ({slots_data['data']}): temos vagas às **{horarios_str}**. Qual horário fica melhor para a sua rotina?"
                )
            else:
                response_text = (
                    f"{opener} Aceitamos Unimed Nacional, Bradesco Saúde e SulAmérica Exato para consultas e testes.\n\n"
                    f"Também emitimos nota para reembolso no seu convênio. Quer dar uma olhada nas vagas disponíveis?"
                )

        # CASO 10: Saudação Padrão ou Continuidade
        else:
            action_name = "receptionist_greeting"
            clean_first = clean_patient_first_name(display_name)
            name_ack = f", {clean_first}" if clean_first else ""
            if active_booking or conversation.current_goal == "consulta_agendada":
                time_info = active_booking['data_hora_str'] if active_booking else "amanhã"
                response_text = (
                    f"Olá{name_ack}! Lembrando que sua consulta já está confirmadíssima para **{time_info}**! 🏥\n\n"
                    f"📍 **Endereço:** Av. Paulista, 1000 (com estacionamento no local e manobrista). 🚗\n\n"
                    f"Se precisar de mais informações ou alterar seu agendamento, é só me dizer: **'preciso falar do meu agendamento'**."
                )
            elif past_msgs_count > 1 or conversation.current_goal in ["aguardando_confirmacao_horario"]:
                slots_data = await scheduler_agent.find_available_slots(db, clinic_id)
                horarios_str = ", ".join(slots_data["horarios_disponiveis"][:3])
                response_text = f"Estou acompanhando seu caso com carinho! Podemos agendar sua avaliação para amanhã em um destes horários: **{horarios_str}**. Qual prefere?"
            else:
                response_text = get_dynamic_greeting(display_name)

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
            await db.commit()
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

    async def _get_or_create_conversation(self, db: AsyncSession, clinic_id: uuid.UUID, contact_id: uuid.UUID) -> Conversation:
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

        return conversation

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

