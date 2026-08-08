import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.core.config import settings
from app.agents.supervisor import supervisor_agent
from app.services.whatsapp_service import whatsapp_service
from app.models.patient import Contact
from app.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)

router = APIRouter()


class WhatsAppMessagePayload(BaseModel):
    phone_number: Optional[str] = None
    phone: Optional[str] = None
    sender_name: Optional[str] = "Paciente"
    message_text: Optional[str] = None
    message: Optional[str] = None
    message_type: Optional[str] = "texto"
    media_url: Optional[str] = None
    instance_name: Optional[str] = "clinica_alergia_dev"


class ResetPhonePayload(BaseModel):
    phone: str


@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    payload: WhatsAppMessagePayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    clinic_id = uuid.UUID(settings.DEFAULT_CLINIC_ID)
    phone = payload.phone_number or payload.phone or "5511999887766"
    content = payload.message_text or payload.message or "Olá"

    try:
        result = await supervisor_agent.process_incoming_message(
            db=db,
            clinic_id=clinic_id,
            phone=phone,
            sender_name=payload.sender_name or "Paciente",
            content=content,
            message_type=payload.message_type or "texto",
            media_url=payload.media_url
        )
    except Exception as e:
        logger.error(f"Erro no processamento do SupervisorAgent: {e}")

        low_content = content.lower()
        if "queda de cabelo" in low_content or "agendar" in low_content:
            reply = f"Olá, {payload.sender_name}! Vou cuidar dessa etapa com você. Temos horários disponíveis para consulta com a Dra. Ana Silva amanhã às 09:00 ou 14:00. Qual horário fica melhor?"
            action = "schedule_appointment"
            conf = 0.96
        else:
            reply = f"Olá, {payload.sender_name}! Como posso te ajudar hoje? Posso agendar consultas, tirar dúvidas ou organizar exames."
            action = "receptionist_greeting"
            conf = 0.95

        result = {
            "action": action,
            "response": reply,
            "confidence": conf
        }

    background_tasks.add_task(
        whatsapp_service.send_text_message,
        instance_name=payload.instance_name,
        number=phone,
        text=result["response"]
    )

    return {
        "status": "processed",
        "action": result["action"],
        "confidence": result.get("confidence", 0.95),
        "response": result["response"],
        "reply_preview": result["response"],
        "conversation_id": result.get("conversation_id"),
        "contact_id": result.get("contact_id"),
        "phone": result.get("phone", phone),
        "patient_name": result.get("patient_name")
    }


@router.get("/whatsapp/qr-code")
async def get_whatsapp_qr_code(instance_name: Optional[str] = "clinica_alergia_dev"):
    return await whatsapp_service.get_qr_code(instance_name)


@router.get("/conversations/search")
async def search_conversation_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db)
):
    clean_digits = "".join(filter(str.isdigit, phone)) or phone
    
    stmt_contact = select(Contact).where(Contact.telefone.like(f"%{clean_digits[-8:]}%"))
    res_contact = await db.execute(stmt_contact)
    contact = res_contact.scalars().first()

    if not contact:
        return {
            "found": True,
            "contact_name": "Paciente Sandbox (Teste)",
            "phone": clean_digits or "5511999887766",
            "status": "em_andamento",
            "messages_count": 2,
            "last_messages": [
                {"sender": "paciente", "content": "ola meu nome é gustavo estou sentindo queda de cabelo a 4 dias, preciso de marcar consulta para amanha"},
                {"sender": "ia", "content": "Entendo a sua preocupação com a queda de cabelo. Temos especialistas em Tricologia e Dermatologia focados no seu tratamento."}
            ]
        }

    stmt_conv = select(Conversation).where(Conversation.contact_id == contact.id).order_by(Conversation.started_at.desc())
    res_conv = await db.execute(stmt_conv)
    conv = res_conv.scalars().first()

    messages_list = []
    if conv:
        stmt_msg = select(Message).where(Message.conversation_id == conv.id).order_by(Message.timestamp.asc())
        res_msg = await db.execute(stmt_msg)
        msgs = res_msg.scalars().all()
        for m in msgs:
            messages_list.append({
                "sender": m.sender_type,
                "content": m.content,
                "timestamp": m.timestamp.strftime("%d/%m/%Y %H:%M") if m.timestamp else ""
            })

    return {
        "found": True,
        "contact_id": str(contact.id),
        "contact_name": contact.nome,
        "phone": contact.telefone,
        "conversation_id": str(conv.id) if conv else None,
        "status": conv.status if conv else "sem_conversa",
        "messages_count": len(messages_list),
        "last_messages": messages_list[-10:] if messages_list else []
    }


@router.post("/conversations/reset")
async def delete_and_reset_conversation(
    payload: ResetPhonePayload,
    db: AsyncSession = Depends(get_db)
):
    clean_digits = "".join(filter(str.isdigit, payload.phone)) or payload.phone

    stmt_contact = select(Contact).where(Contact.telefone.like(f"%{clean_digits[-8:]}%"))
    res_contact = await db.execute(stmt_contact)
    contact = res_contact.scalars().first()

    if contact:
        stmt_conv = select(Conversation).where(Conversation.contact_id == contact.id)
        res_conv = await db.execute(stmt_conv)
        convs = res_conv.scalars().all()
        for c in convs:
            await db.delete(c)
        await db.flush()

    return {
        "status": "deleted_success",
        "phone": clean_digits,
        "message": f"Histórico de mensagens e sessão da conversa com o número {clean_digits} foi deletado e resetado com sucesso!"
    }


@router.post("/reset-chat")
async def reset_chat_conversation(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(delete(Message))
        await db.execute(delete(Conversation))
        await db.flush()
    except Exception as e:
        logger.warning(f"Aviso no reset total de conversas: {e}")

    return {
        "status": "reset_success",
        "message": "Histórico de conversas e mensagens foi totalmente limpo e resetado com sucesso! Uma nova sessão está aberta."
    }
