from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.ai_orchestrator import LifelineAIOrchestrator
from app.services.whatsapp_gateway import whatsapp_gateway

router = APIRouter()

class EvolutionWebhookMessageData(BaseModel):
    key: Dict[str, Any] = Field(default_factory=dict)
    pushName: Optional[str] = None
    message: Dict[str, Any] = Field(default_factory=dict)

class EvolutionWebhookPayload(BaseModel):
    event: str = "messages.upsert"
    data: Dict[str, Any] = Field(default_factory=dict)

@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook público para recepção de mensagens do WhatsApp (Evolution API / Meta Cloud API).
    Processa os 11 passos do AI Orchestrator e envia a resposta de volta ao WhatsApp.
    """
    # 1. Extração padronizada de telefone, nome e mensagem recebida
    phone = ""
    sender_name = "Paciente WhatsApp"
    message_text = ""

    # Formato Evolution API
    if "data" in payload and isinstance(payload["data"], dict):
        data = payload["data"]
        key = data.get("key", {})
        phone = key.get("remoteJid", "").split("@")[0]
        sender_name = data.get("pushName", sender_name)
        msg_obj = data.get("message", {})
        message_text = msg_obj.get("conversation") or msg_obj.get("extendedTextMessage", {}).get("text", "")
    
    # Formato genérico / simplificado
    if not phone:
        phone = str(payload.get("phone") or payload.get("number") or "5511999998888")
        sender_name = payload.get("sender_name") or payload.get("name") or sender_name
        message_text = payload.get("text") or payload.get("message") or ""

    if not message_text:
        return {"status": "ignored", "reason": "Sem texto de mensagem"}

    # 2. Executa os 11 passos de raciocínio da IA e atualiza o estado do paciente
    orchestration_result = await LifelineAIOrchestrator.process_incoming_message(
        db=db,
        phone=phone,
        message_text=message_text,
        patient_name=sender_name
    )

    # 3. Despacha a resposta da IA de volta para o WhatsApp do paciente via Gateway
    dispatch_status = await whatsapp_gateway.dispatch_ai_response(
        phone=phone,
        response_text=orchestration_result["ai_response"],
        tool_outputs=orchestration_result.get("tool_outputs")
    )

    return {
        "status": "processed",
        "phone": phone,
        "current_stage": orchestration_result["current_stage"],
        "detected_intent": orchestration_result["detected_intent"],
        "ai_response": orchestration_result["ai_response"],
        "dispatch_status": dispatch_status
    }
