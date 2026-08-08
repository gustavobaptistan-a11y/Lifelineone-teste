from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.ai_orchestrator import LifelineAIOrchestrator

router = APIRouter()

class IncomingMessageRequest(BaseModel):
    phone: str = Field(..., json_schema_extra={"example": "5511999998888"})
    message: str = Field(..., json_schema_extra={"example": "Gostaria de agendar uma consulta"})
    patient_name: Optional[str] = Field(None, json_schema_extra={"example": "Gustavo Baptista"})

class OrchestratorResponse(BaseModel):
    patient_id: int
    current_stage: str
    detected_intent: str
    tools_executed: list
    tool_outputs: dict
    ai_response: str

@router.post("/message", response_model=OrchestratorResponse)
async def process_message(
    payload: IncomingMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ponto de entrada para mensagens recebidas dos canais (WhatsApp, Instagram, Web).
    Aciona o Lifeline AI Orchestrator com raciocínio de 11 passos.
    """
    result = await LifelineAIOrchestrator.process_incoming_message(
        db=db,
        phone=payload.phone,
        message_text=payload.message,
        patient_name=payload.patient_name
    )
    return result
