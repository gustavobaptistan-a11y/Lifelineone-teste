from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.ticket_service import TicketService

router = APIRouter()

class TicketCreateRequest(BaseModel):
    patient_id: int
    reason: str = Field("Solicitação de atendimento humano", json_schema_extra={"example": "Paciente solicitou falar com a recepção"})

class TicketTakeoverRequest(BaseModel):
    agent_name: str = Field("Dra. Paula (Recepção)", json_schema_extra={"example": "Dra. Paula"})

class TicketResponse(BaseModel):
    id: int
    patient_id: int
    status: str
    assigned_agent: Optional[str]
    reason: Optional[str]

@router.post("/create", response_model=TicketResponse)
async def create_ticket(
    payload: TicketCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Abre um ticket de atendimento para o paciente na plataforma.
    """
    ticket = await TicketService.create_ticket(db, payload.patient_id, payload.reason)
    return ticket

@router.post("/{ticket_id}/takeover", response_model=TicketResponse)
async def takeover_ticket(
    ticket_id: int,
    payload: TicketTakeoverRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Atendente humano assume a conversa. O Lifeline AI Orchestrator pausa respostas automáticas.
    """
    ticket = await TicketService.takeover_ticket(db, ticket_id, payload.agent_name)
    return ticket

@router.post("/{ticket_id}/release", response_model=TicketResponse)
async def release_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Atendente humano devolve o controle da conversa. O Lifeline AI Orchestrator reassume as respostas automáticas.
    """
    ticket = await TicketService.release_ticket(db, ticket_id)
    return ticket

@router.get("/active", response_model=List[TicketResponse])
async def get_active_tickets(db: AsyncSession = Depends(get_db)):
    """
    Retorna a lista de tickets ativos aguardando ou assumidos por atendimento humano.
    """
    return await TicketService.get_active_tickets(db)
