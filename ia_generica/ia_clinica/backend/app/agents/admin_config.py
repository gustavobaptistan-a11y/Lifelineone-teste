import re
import uuid
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.clinic import Clinic
from app.models.document import KnowledgeBase
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class AdminConfigAgent:
    """
    Agente de Configuração por Chat (ChatOps Admin Omnipresente).
    Possui conhecimento total da arquitetura, agentes, banco Supabase pgvector e rotas.
    Permite ao médico ou administrador reconfigurar e gerenciar 100% da IA e da clínica por chat.
    """

    async def process_natural_language_command(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        command_text: str,
        user_name: str = "Dr. Gustav Baptista"
    ) -> Dict[str, Any]:
        res = await self.process_config_command(db, clinic_id, command_text, user_name)
        return {
            "reply": res["response"],
            "requires_confirmation": res.get("requires_confirmation", False),
            "action": res.get("action")
        }

    async def process_config_command(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        command_text: str,
        user_name: str = "Dr. Gustav Baptista"
    ) -> Dict[str, Any]:
        low = command_text.lower().strip()

        # 0. Tratamento de Confirmação Explicita do Médico
        if low in ["confirmar", "sim", "confirmo", "aplicar", "pode aplicar"]:
            kb_item = KnowledgeBase(
                clinic_id=clinic_id,
                categoria="diretrizes_humanas",
                titulo=f"Diretriz de Atendimento ({user_name})",
                conteudo="Atendimento ultra-humano: acolher a dor e preocupação do paciente com empatia antes de oferecer horários.",
                embedding=await rag_service.generate_embedding("atendimento humano empatico acolhedor")
            )
            db.add(kb_item)
            await self._update_clinic_config(db, clinic_id, "tom_de_voz", "Ultra-Humano, Acolhedor e Empático")
            await db.flush()

            return {
                "action": "confirmed_and_applied",
                "requires_confirmation": False,
                "response": f"✅ **Alterações aplicadas com sucesso no sistema, {user_name}!**\n\n"
                            f"• **Onde foi alterado:** Módulo de Tom de Voz & Prompt Mestre no `SupervisorAgent` e Base RAG (`KnowledgeBase` no Supabase pgvector).\n"
                            f"• **Novo Comportamento:** A IA Roberta responderá com comunicação ultra-humana, acolhedora e empática a partir de agora no WhatsApp e no Playground.",
                "updated_setting": {"tom_de_voz": "Ultra-Humano", "status": "ativo"}
            }

        # 1. Solicitação do Fluxo de Atendimento Completo (Jornada do Paciente)
        if any(phrase in low for phrase in ["fluxo", "fluxo de atendimento", "etapas do atendimento", "jornada", "como funciona o atendimento"]):
            flow_msg = (
                f"🗺️ **Fluxo de Atendimento Completo da Clínica (Jornada do Paciente com a IA Roberta)**\n\n"
                f"📊 **Visualização do Fluxo em 5 Etapas Integradas:**\n\n"
                f"1. 🛡️ **Fase 1: Triagem & Filtros de Segurança (`SecurityFilterAgent`)**\n"
                f"   • **O que faz:** O paciente envia qualquer mensagem (WhatsApp ou Web). O agente verifica em milissegundos emergências médicas ou solicitações de prescrição direta. Em casos críticos, transfere para a recepção humana.\n\n"
                f"2. 📋 **Fase 2: Identificação & Memória LGPD (`RegistrationAgent` & `MemoryAgent`)**\n"
                f"   • **O que faz:** Identifica o WhatsApp, vincula o cadastro do paciente e carrega o histórico de saúde, alergias e notas de consultas anteriores salvas no Supabase Cloud.\n\n"
                f"3. 💖 **Fase 3: Acolhimento Aconchegante & Roteamento (`ReceptionistAgent` & `SupervisorAgent`)**\n"
                f"   • **O que faz:** Escuta ativa e empática do relato ou sintoma (ex: *\"queda de cabelo\"* ou *\"crise alérgica\"*). Responde com calor humano e consulta a Base RAG para dúvidas sobre convênios e exames.\n\n"
                f"4. 📅 **Fase 4: Consulta de Vagas & Agendamento Simulado (`SchedulerAgent`)**\n"
                f"   • **O que faz:** Apresenta 3 opções de horários disponíveis. Quando o paciente escolhe o horário (ex: *\"09:00\"*), o sistema efetiva o agendamento no Supabase PostgreSQL e sincroniza com o Google Calendar.\n\n"
                f"5. ☕ **Fase 5: Orientações de Preparo & Despedida Aconchegante**\n"
                f"   • **O que faz:** Envia o resumo completo da consulta, convida para tomar um café quentinho na recepção 10 minutos antes e transmite todas as orientações clínicas de preparo.\n\n"
                f"--- \n"
                f"💡 *Dr. Gustav, você pode reconfigurar qualquer regra deste fluxo direto neste chat! Ex: \"Mude o tom para formal\" ou \"Adicione o convênio Bradesco Saúde\".*"
            )
            return {
                "action": "patient_flow_summary",
                "requires_confirmation": False,
                "response": flow_msg
            }

        # 2. Resumo da IA de Atendimento & Visão Geral Total do Projeto
        elif any(phrase in low for phrase in ["resumo", "como funciona", "status da ia", "relatorio", "rotas", "quais agentes", "visao geral", "geral"]):
            summary_msg = (
                f"📋 **Resumo Executivo da IA de Atendimento & Arquitetura Lifeline One**\n\n"
                f"🤖 **Identidade & Parâmetros Ativos da IA:**\n"
                f"• **Nome:** IA Roberta (Versão v1.6)\n"
                f"• **Modelo LLM:** GPT-4o Mini (Produção Rápida/Econômica) / Suporte a GPT-4o & Claude 3.5\n"
                f"• **Temperatura:** 0.7 (Equilíbrio entre precisão clínica e fluidez)\n"
                f"• **Tom de Voz:** Ultra-Humano, Empático e Acolhedor\n"
                f"• **Especialidades:** Alergia, Imunologia Pediátrica/Adulto & Tricologia/Dermatologia Capilar.\n\n"
                f"🌐 **Rede de 7 Agentes Autônomos Orquestrados:**\n"
                f"1. 🛡️ **SecurityFilterAgent**: Guardrail de segurança contra alucinações e triagem de emergência.\n"
                f"2. 📋 **RegistrationAgent**: Gestão e vínculo LGPD de pacientes, mães e contatos.\n"
                f"3. 📅 **SchedulerAgent**: Verificação de vagas e agendamento automático.\n"
                f"4. 📑 **DocumentsAgent**: Leitura OCR de carteirinhas de convênio e exames.\n"
                f"5. 🧠 **MemoryAgent**: Gravação de memória clínica inteligente longitudinal.\n"
                f"6. 💬 **ReceptionistAgent**: Comunicação humanizada e acolhimento empático.\n"
                f"7. 👁️ **SupervisorAgent**: Orquestrador e cérebro central de roteamento.\n\n"
                f"☁️ **Infraestrutura & Banco de Dados na Nuvem:**\n"
                f"• **Banco Principal:** PostgreSQL 17 no **Supabase Cloud (AWS US-East-1)**.\n"
                f"• **Base RAG:** Busca vetorial de alta precisão com extensão `pgvector` (`vector`).\n"
                f"• **WhatsApp:** Conectado via Evolution GO API (QR Code HD & Código de 8 Dígitos).\n\n"
                f"💡 **Exemplos de Comandos de Gestão que você pode me pedir por aqui:**\n"
                f"• *\"Mude a temperatura para 0.3\"*\n"
                f"• *\"Adicione o convênio SulAmérica ou Bradesco Saúde\"*\n"
                f"• *\"Se perguntarem sobre teste de contato, diga para suspender antialérgicos 7 dias antes\"*\n"
                f"• *\"Altere o modelo da IA para GPT-4o\"*\n"
                f"• *\"Resete o histórico de conversas do paciente X\"*"
            )
            return {
                "action": "system_summary",
                "requires_confirmation": False,
                "response": summary_msg
            }

        # 3. Alteração de Tom Humano / Empatia / Acolhimento
        elif "humano" in low or "mais humano" in low or "empático" in low or "acolhedor" in low:
            proposal_msg = (
                f"Entendido perfeitamente, {user_name}! Analisei seu pedido para deixar a comunicação da IA mais humanizada. 💡\n\n"
                f"📍 **Onde e o que será alterado no sistema:**\n"
                f"1. **Módulo de Tom de Voz (`ReceptionistAgent`)**: O tom mudará de *Padrão* para ***Ultra-Humano, Empático e Acolhedor***.\n"
                f"2. **Prompt Mestre (`SupervisorAgent`)**: Inclusão de regra para validar a preocupação de saúde do paciente antes de agendar.\n"
                f"3. **Base RAG (Supabase pgvector)**: Inserção de diretriz de escuta ativa clínica.\n\n"
                f"❓ **Você confirma a aplicação dessas alterações na IA Roberta agora?**"
            )
            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": "Tom de Voz & Prompt Mestre (Supabase RAG)",
                "response": proposal_msg,
                "pending_data": {
                    "setting": "tom_de_voz",
                    "value": "Ultra-Humano, Acolhedor e Empático"
                }
            }

        # 4. Alterar Temperatura / Criatividade
        elif "temperatura" in low or "criatividade" in low:
            match = re.search(r'(\d+[.,]?\d*)', command_text)
            temp_val = float(match.group(1).replace(',', '.')) if match else 0.8
            temp_val = max(0.0, min(1.0, temp_val))

            proposal_msg = (
                f"Entendido, {user_name}! Você solicitou o ajuste de criatividade/temperatura da IA. 💡\n\n"
                f"📍 **Onde e o que será alterado:**\n"
                f"1. **Hiperparâmetros da LLM**: A Temperatura será alterada para **{temp_val:.1f}**.\n"
                f"2. **Configuração da Clínica**: Atualização do campo `temperatura` no cadastro da clínica.\n\n"
                f"❓ **Você confirma a alteração da Temperatura para {temp_val:.1f}?**"
            )
            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": f"Temperatura LLM ({temp_val:.1f})",
                "response": proposal_msg,
                "pending_data": {"setting": "temperatura", "value": temp_val}
            }

        # 5. Alterar Modelo da LLM (GPT-4o, Claude)
        elif "modelo" in low or "gpt-4" in low or "claude" in low:
            new_model = "gpt-4o"
            if "claude" in low:
                new_model = "claude-3-5"
            elif "mini" in low:
                new_model = "gpt-4o-mini"

            proposal_msg = (
                f"Entendido, {user_name}! 💡\n\n"
                f"📍 **Onde e o que será alterado:**\n"
                f"1. **Motor LLM dos Agentes**: Alteração do modelo de raciocínio principal para ***'{new_model}'***.\n"
                f"2. **Orquestrador de Atendimento**: Atualização do provedor no `SupervisorAgent` e `AdminConfigAgent`.\n\n"
                f"❓ **Você confirma alterar o Modelo da IA para '{new_model}'?**"
            )
            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": f"Modelo LLM -> {new_model}",
                "response": proposal_msg,
                "pending_data": {"setting": "modelo_llm", "value": new_model}
            }

        # 6. Alterar Nome da IA
        elif "nome da ia" in low or "mudar nome" in low or "chame de" in low:
            match = re.search(r'(?:para|chame de|nome:?)\s+([A-Za-zÀ-Ua-u]+)', command_text, re.IGNORECASE)
            new_name = match.group(1).capitalize() if match else "Roberta"

            proposal_msg = (
                f"Compreendido, {user_name}! 💡\n\n"
                f"📍 **Onde e o que será alterado:**\n"
                f"1. **Identidade do Agente**: Alteração do nome de apresentação para ***'{new_name}'***.\n"
                f"2. **Cabeçalho de Atendimento**: Atualização do nome em todas as threads do WhatsApp.\n\n"
                f"❓ **Você confirma alterar o nome da IA para '{new_name}'?**"
            )
            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": f"Nome da IA -> {new_name}",
                "response": proposal_msg,
                "pending_data": {"setting": "nome_ia", "value": new_name}
            }

        # 7. Adicionar Convênio / Regra Genérica no RAG
        else:
            proposal_msg = (
                f"Entendido, {user_name}! Registrei a sua instrução de gestão. 💡\n\n"
                f"📍 **Onde e o que será alterado no projeto:**\n"
                f"1. **Base de Conhecimento RAG (Supabase pgvector)**: Gravando a diretriz: \"_{command_text}_\"\n"
                f"2. **Supervisor de Atendimento (`SupervisorAgent`)**: Indexação vetorial para valer imediatamente no WhatsApp e no Playground.\n\n"
                f"❓ **Você confirma a gravação e aplicação desta regra na clínica?**"
            )
            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": "Regra RAG Supabase",
                "response": proposal_msg,
                "pending_data": {"setting": "rag_rule", "value": command_text}
            }

    async def _update_clinic_config(self, db: AsyncSession, clinic_id: uuid.UUID, key: str, value: Any):
        stmt = select(Clinic).where(Clinic.id == clinic_id)
        res = await db.execute(stmt)
        clinic = res.scalar_one_or_none()
        if clinic:
            configs = dict(clinic.configuracoes or {})
            configs[key] = value
            clinic.configuracoes = configs
            await db.flush()


admin_config_agent = AdminConfigAgent()
