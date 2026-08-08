import re
import uuid
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.clinic import Clinic
from app.models.document import KnowledgeBase
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class AdminConfigAgent:
    """
    Agente de Configuração por ChatOps (Copiloto Admin Omnipresente).
    Possui conhecimento total da arquitetura, agentes, banco Supabase pgvector e rotas.
    Permite ao médico ou administrador reconfigurar 100% da IA Roberta e da clínica em tempo real por conversa natural.
    """

    def __init__(self):
        # Armazena estado de alterações pendentes de confirmação por clinica
        self.pending_changes: Dict[str, Dict[str, Any]] = {}

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
        cid_str = str(clinic_id)

        # 0. Tratamento de Confirmação Explicita pelo Médico
        if low in ["confirmar", "sim", "confirmo", "aplicar", "pode aplicar", "sim por favor", "ok aplicar", "sim, pode aplicar"]:
            pending = self.pending_changes.pop(cid_str, None)
            if pending:
                setting_key = pending.get("setting")
                setting_val = pending.get("value")
                cat = pending.get("category", "diretrizes_humanas")
                title = pending.get("title", f"Diretriz Admin ({user_name})")
                content = pending.get("content", str(setting_val))

                # Atualiza tabela Clinic.configuracoes
                if setting_key and setting_val is not None:
                    await self._update_clinic_config(db, clinic_id, setting_key, setting_val)

                # Grava item vetorial na Base RAG Supabase
                kb_item = KnowledgeBase(
                    clinic_id=clinic_id,
                    categoria=cat,
                    titulo=title,
                    conteudo=content,
                    embedding=await rag_service.generate_embedding(content)
                )
                db.add(kb_item)
                await db.flush()

                return {
                    "action": "confirmed_and_applied",
                    "requires_confirmation": False,
                    "response": (
                        f"✅ **Alterações aplicadas com sucesso, {user_name}!**\n\n"
                        f"• **Alvo do Ajuste:** {pending.get('target_desc', 'Configuração da IA')}\n"
                        f"• **Onde foi gravado:** Tabela `clinic.configuracoes` e Base RAG (`KnowledgeBase` no Supabase pgvector).\n"
                        f"• **Impacto Impartido:** A IA Roberta usará essa nova diretriz imediatamente em todas as novas conversas no WhatsApp e no Simulador."
                    ),
                    "updated_setting": {setting_key: setting_val, "status": "ativo"}
                }
            else:
                # Se não havia pendência, aplica diretriz padrão de escuta empática
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
                    "response": (
                        f"✅ **Configuração de Atendimento Humanizado ativada, {user_name}!**\n\n"
                        f"• **Onde foi alterado:** Módulo de Tom de Voz & Prompt Mestre do `SupervisorAgent` e Base RAG Supabase.\n"
                        f"• **Novo Comportamento:** A IA responderá com escuta ativa e empatia clínica prioritária."
                    )
                }

        # 1. Solicitação do Fluxo de Atendimento Completo (Jornada do Paciente)
        if any(phrase in low for phrase in ["fluxo", "etapas do atendimento", "jornada", "como funciona o atendimento"]):
            flow_msg = (
                f"🗺️ **Fluxo de Atendimento Completo da Clínica (Jornada da IA Roberta)**\n\n"
                f"📊 **Visualização do Fluxo em 5 Etapas Integradas:**\n\n"
                f"1. 🛡️ **Fase 1: Triagem & Filtros de Segurança (`SecurityFilterAgent`)**\n"
                f"   • Milissegundos de validação de emergências, pedidos de prescrição e prompt injections.\n\n"
                f"2. 📋 **Fase 2: Identificação & Memória LGPD (`RegistrationAgent` & `MemoryAgent`)**\n"
                f"   • Cadastro automático de contatos, histórico de saúde e sintomas de consultas passadas.\n\n"
                f"3. 💖 **Fase 3: Acolhimento Aconchegante & RAG (`ReceptionistAgent` & `SupervisorAgent`)**\n"
                f"   • Escuta empática do motivo do paciente e busca vetorial RAG sobre dúvidas e convênios.\n\n"
                f"4. 📅 **Fase 4: Consulta de Vagas & Agendamento (`SchedulerAgent`)**\n"
                f"   • Apresentação de opções de horários com sincronização imediata no Supabase PostgreSQL.\n\n"
                f"5. ☕ **Fase 5: Orientações de Preparo & Despedida Aconchegante**\n"
                f"   • Envio de orientações pré-consulta e convite para um café na recepção 10 minutos antes.\n\n"
                f"--- \n"
                f"💡 *{user_name}, peça qualquer alteração por este chat (ex: 'Mude o preço para R$ 400' ou 'Adicione convênio Bradesco').*"
            )
            return {
                "action": "patient_flow_summary",
                "requires_confirmation": False,
                "response": flow_msg
            }

        # 2. Status Completo e Visão Geral Total da IA
        elif any(phrase in low for phrase in ["resumo", "status da ia", "relatorio", "quais agentes", "visao geral", "geral"]):
            current_cfg = await self._get_clinic_config(db, clinic_id)
            nome_ia = current_cfg.get("nome_ia", "Roberta")
            tom = current_cfg.get("tom_de_voz", "Ultra-Humano, Empático e Acolhedor")
            preco = current_cfg.get("preco_consulta", "R$ 350,00 (com retorno em 15 dias)")
            endereco = current_cfg.get("endereco", "Av. Paulista, 1000 com estacionamento e manobrista")
            modelo = current_cfg.get("modelo_llm", "GPT-4o Mini (Produção Rápida)")
            temp = current_cfg.get("temperatura", 0.7)
            convenios = current_cfg.get("convenios_aceitos", "Bradesco Saúde, SulAmérica Exato, Unimed Nacional, Particular/Reembolso")

            summary_msg = (
                f"📋 **Resumo Executivo & Parâmetros Ativos da IA Roberta**\n\n"
                f"🤖 **Identidade & Hiperparâmetros em Execução:**\n"
                f"• **Nome da Atendente:** IA {nome_ia}\n"
                f"• **Modelo LLM:** {modelo}\n"
                f"• **Temperatura:** {temp} (Equilíbrio entre precisão clínica e fluidez)\n"
                f"• **Tom de Voz:** {tom}\n"
                f"• **Valor da Consulta:** {preco}\n"
                f"• **Localização:** {endereco}\n"
                f"• **Convênios Aceitos:** {convenios}\n\n"
                f"🌐 **Rede de 7 Agentes Autônomos Orquestrados:**\n"
                f"1. 🛡️ **SecurityFilterAgent**: Guardrail contra alucinações e emergências.\n"
                f"2. 📋 **RegistrationAgent**: Gestão de vínculo LGPD e telefones.\n"
                f"3. 📅 **SchedulerAgent**: Verificação e gravação de vagas.\n"
                f"4. 📑 **DocumentsAgent**: Leitura de exames e carteirinhas.\n"
                f"5. 🧠 **MemoryAgent**: Memória clínica longitudinal.\n"
                f"6. 💬 **ReceptionistAgent**: Comunicação humanizada.\n"
                f"7. 👁️ **SupervisorAgent**: Cérebro central de roteamento.\n\n"
                f"💡 **Exemplos de Comandos que você pode executar agora:**\n"
                f"• *\"Mudar nome da IA para Carolina\"*\n"
                f"• *\"Mudar valor da consulta para R$ 400\"*\n"
                f"• *\"Adicionar convênio Amil e Omint\"*\n"
                f"• *\"Definir endereço para Rua Oscar Freire, 500\"*\n"
                f"• *\"Para teste alérgico suspender antialérgicos 7 dias antes\"*\n"
                f"• *\"Alterar modelo para GPT-4o\"*\n"
                f"• *\"Alterar temperatura para 0.3\"*"
            )
            return {
                "action": "system_summary",
                "requires_confirmation": False,
                "response": summary_msg
            }

        # 3. Alteração de Nome da IA
        elif any(k in low for k in ["nome da ia", "mudar nome", "nome da atendente", "chame de", "chamar de"]):
            match = re.search(r'(?:nome da ia para|nome da atendente para|mudar nome para|chame de|chamar de|para)\s+([A-Za-zÀ-ú]+)', command_text, re.IGNORECASE)
            new_name = match.group(1).strip().capitalize() if match else "Roberta"
            
            self.pending_changes[cid_str] = {
                "setting": "nome_ia",
                "value": new_name,
                "category": "identidade_ia",
                "title": f"Nome da Atendente IA -> {new_name}",
                "content": f"O nome oficial da atendente virtual da clínica é {new_name}.",
                "target_desc": f"Nome da IA para **'{new_name}'**"
            }

            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": f"Nome da Atendente IA -> '{new_name}'",
                "response": (
                    f"Entendido, {user_name}! Solicitou alterar o nome de apresentação da atendente. 💡\n\n"
                    f"📍 **O que será alterado:**\n"
                    f"• **Campo `nome_ia`**: Atualizado para **'{new_name}'** na tabela de configurações da clínica.\n"
                    f"• **Cabeçalho de Atendimento**: Todas as saudações no WhatsApp apresentarão: *'Olá! Sou a {new_name}...'*.\n\n"
                    f"❓ **Confirma a alteração do nome da IA para '{new_name}'?** (Responda 'Sim' ou clique em Confirmar)"
                ),
                "pending_data": {"setting": "nome_ia", "value": new_name}
            }

        # 4. Alteração de Valor de Consulta & Pagamentos
        elif any(k in low for k in ["valor", "preço", "preco", "quanto custa", "r$", "custo consulta"]):
            match = re.search(r'r\$\s*(\d+[\.,]?\d*)|\b(\d{3,4})\b', command_text, re.IGNORECASE)
            val_str = match.group(1) or match.group(2) if match else "400"
            formatted_price = f"R$ {val_str},00 (com direito a retorno em 15 dias)"

            self.pending_changes[cid_str] = {
                "setting": "preco_consulta",
                "value": formatted_price,
                "category": "precos_e_pagamento",
                "title": "Tabela de Preço da Consulta Particular",
                "content": f"A consulta particular é {formatted_price}. Fornecemos nota fiscal para reembolso integral pelo convênio.",
                "target_desc": f"Valor da Consulta -> **{formatted_price}**"
            }

            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": f"Preço da Consulta -> {formatted_price}",
                "response": (
                    f"Entendido, {user_name}! Você solicitou o reajuste do valor da consulta particular. 💡\n\n"
                    f"📍 **O que será alterado:**\n"
                    f"• **Configuração da Clínica**: `preco_consulta` = **{formatted_price}**.\n"
                    f"• **Base RAG & Dúvidas Operacionais**: A IA responderá {formatted_price} sempre que pacientes perguntarem o valor.\n\n"
                    f"❓ **Confirma aplicar o novo valor de consulta ({formatted_price})?**"
                ),
                "pending_data": {"setting": "preco_consulta", "value": formatted_price}
            }

        # 5. Adicionar / Gerenciar Convênios Aceitos
        elif any(k in low for k in ["convênio", "convenio", "plano de saúde", "planos", "aceita amil", "bradesco", "sulamérica", "unimed", "omint", "porto seguro"]):
            self.pending_changes[cid_str] = {
                "setting": "convenios_aceitos",
                "value": command_text,
                "category": "convenios",
                "title": "Diretriz de Convênios Aceitos na Clínica",
                "content": f"Diretriz de Convênios Aceitos: {command_text}. Aceitamos consultas particulares com nota fiscal para reembolso no convênio.",
                "target_desc": f"Regra de Convênios -> **'{command_text}'**"
            }

            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": "Atualização de Convênios Aceitos",
                "response": (
                    f"Entendido, {user_name}! Solicitou a atualização dos convênios e planos de saúde aceitos. 💡\n\n"
                    f"📍 **O que será alterado:**\n"
                    f"• **Tabela RAG de Convênios (`KnowledgeBase`)**: Indexação vetorial para a instrução: *'{command_text}'*.\n"
                    f"• **Roteamento de Dúvidas**: A IA confirmará cobertura para os planos especificados.\n\n"
                    f"❓ **Confirma salvar a nova regra de convênios na clínica?**"
                ),
                "pending_data": {"setting": "convenios_aceitos", "value": command_text}
            }

        # 6. Alteração de Endereço, Localização e Horário
        elif any(k in low for k in ["endereço", "endereco", "localização", "localizacao", "onde fica", "estacionamento", "horário de funcionamento", "horario"]):
            self.pending_changes[cid_str] = {
                "setting": "endereco",
                "value": command_text,
                "category": "localizacao",
                "title": "Localização, Endereço e Horários da Clínica",
                "content": f"Informações de Localização e Horário da Clínica: {command_text}.",
                "target_desc": f"Endereço & Horários -> **'{command_text}'**"
            }

            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": "Endereço e Horários de Atendimento",
                "response": (
                    f"Compreendido, {user_name}! Solicitou atualização de endereço ou horários. 💡\n\n"
                    f"📍 **O que será alterado:**\n"
                    f"• **Tabela de Localização RAG**: Gravando *'{command_text}'* na base vetorial.\n"
                    f"• **Dúvidas de Pacientes**: A IA informará este local e horários ao responder dúvidas de localização.\n\n"
                    f"❓ **Confirma a atualização destas informações de localização?**"
                ),
                "pending_data": {"setting": "endereco", "value": command_text}
            }

        # 7. Tom de Voz & Estilo de Comunicação
        elif any(k in low for k in ["tom", "estilo", "formal", "descontraído", "descontraido", "humano", "empático", "empatico", "acolhedor", "objetivo"]):
            new_tone = "Ultra-Humano, Empático e Acolhedor"
            if "formal" in low: new_tone = "Formal, Respeitoso e Executivo"
            elif "objetivo" in low or "direto" in low: new_tone = "Objetivo, Claro e Eficiente"
            elif "descontraído" in low or "descontraido" in low: new_tone = "Descontraído, Leve e Amigável"

            self.pending_changes[cid_str] = {
                "setting": "tom_de_voz",
                "value": new_tone,
                "category": "diretrizes_humanas",
                "title": f"Estilo e Tom de Voz da IA -> {new_tone}",
                "content": f"Regra de Comunicação da IA: Adotar tom {new_tone} na conversa com todos os pacientes.",
                "target_desc": f"Tom de Voz -> **{new_tone}**"
            }

            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": f"Tom de Voz -> {new_tone}",
                "response": (
                    f"Entendido perfeitamente, {user_name}! Solicitou a mudança de tom de voz da IA. 💡\n\n"
                    f"📍 **O que será alterado:**\n"
                    f"• **Módulo de Comunicação (`ReceptionistAgent`)**: Ajustado para o perfil ***{new_tone}***.\n"
                    f"• **Prompt Mestre (`SupervisorAgent`)**: Re-alinhamento da postura das respostas.\n\n"
                    f"❓ **Confirma aplicar o Tom de Voz {new_tone}?**"
                ),
                "pending_data": {"setting": "tom_de_voz", "value": new_tone}
            }

        # 8. Hiperparâmetros LLM (Modelo & Temperatura)
        elif any(k in low for k in ["modelo", "gpt-4", "claude", "temperatura", "criatividade"]):
            if "temperatura" in low or "criatividade" in low:
                match = re.search(r'(\d+[.,]?\d*)', command_text)
                temp_val = float(match.group(1).replace(',', '.')) if match else 0.8
                temp_val = max(0.0, min(1.0, temp_val))
                
                self.pending_changes[cid_str] = {
                    "setting": "temperatura",
                    "value": temp_val,
                    "category": "hiperparametros",
                    "title": f"Temperatura LLM ({temp_val:.1f})",
                    "content": f"A temperatura de raciocínio da IA é {temp_val:.1f}.",
                    "target_desc": f"Temperatura LLM -> **{temp_val:.1f}**"
                }

                return {
                    "action": "proposal_requires_confirmation",
                    "requires_confirmation": True,
                    "proposed_target": f"Temperatura LLM -> {temp_val:.1f}",
                    "response": (
                        f"Entendido, {user_name}! Solicitou o ajuste de criatividade/temperatura da IA. 💡\n\n"
                        f"📍 **O que será alterado:**\n"
                        f"• **Temperatura LLM**: Definida para **{temp_val:.1f}**.\n\n"
                        f"❓ **Confirma alterar a Temperatura para {temp_val:.1f}?**"
                    )
                }
            else:
                new_model = "gpt-4o"
                if "claude" in low: new_model = "claude-3-5"
                elif "mini" in low: new_model = "gpt-4o-mini"

                self.pending_changes[cid_str] = {
                    "setting": "modelo_llm",
                    "value": new_model,
                    "category": "hiperparametros",
                    "title": f"Modelo LLM Principal -> {new_model}",
                    "content": f"O modelo LLM principal da IA é {new_model}.",
                    "target_desc": f"Modelo LLM -> **{new_model}**"
                }

                return {
                    "action": "proposal_requires_confirmation",
                    "requires_confirmation": True,
                    "proposed_target": f"Modelo LLM -> {new_model}",
                    "response": (
                        f"Entendido, {user_name}! Solicitou trocar o motor de Inteligência Artificial. 💡\n\n"
                        f"📍 **O que será alterado:**\n"
                        f"• **Motor LLM dos Agentes**: Alteração do modelo principal para ***'{new_model}'***.\n\n"
                        f"❓ **Confirma alterar o Modelo da IA para '{new_model}'?**"
                    )
                }

        # 9. Instrução Clínica / Preparo de Exames / Regra RAG Geral
        else:
            self.pending_changes[cid_str] = {
                "setting": "diretriz_geral",
                "value": command_text,
                "category": "diretrizes_clinicas",
                "title": f"Diretriz Clínica / Regra de Negócio ({user_name})",
                "content": command_text,
                "target_desc": f"Diretriz de Atendimento -> **'{command_text}'**"
            }

            return {
                "action": "proposal_requires_confirmation",
                "requires_confirmation": True,
                "proposed_target": "Diretriz RAG & Regra de Negócio",
                "response": (
                    f"Entendido, {user_name}! Registrei a sua instrução de gestão. 💡\n\n"
                    f"📍 **O que será alterado no projeto:**\n"
                    f"1. **Base de Conhecimento RAG (Supabase pgvector)**: Gravando a diretriz: *\"{command_text}\"*\n"
                    f"2. **Supervisor de Atendimento (`SupervisorAgent`)**: Indexação vetorial imediata para aplicação no WhatsApp e no Playground.\n\n"
                    f"❓ **Confirma a gravação e aplicação desta regra na clínica?** (Responda 'Sim' ou clique em Confirmar)"
                ),
                "pending_data": {"setting": "diretriz_geral", "value": command_text}
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

    async def _get_clinic_config(self, db: AsyncSession, clinic_id: uuid.UUID) -> Dict[str, Any]:
        stmt = select(Clinic).where(Clinic.id == clinic_id)
        res = await db.execute(stmt)
        clinic = res.scalar_one_or_none()
        if clinic and clinic.configuracoes:
            return dict(clinic.configuracoes)
        return {}


admin_config_agent = AdminConfigAgent()
