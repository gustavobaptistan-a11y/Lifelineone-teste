from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.ticket import SupportTicket, TicketStatus
from app.models.patient import Patient
from app.services.patient_service import PatientService
from app.core.websocket_manager import ws_manager

class TicketService:
    """
    Serviço de Gestão de Atendimento Híbrido (IA + Transbordo Humano).
    Permite à equipe de recepção/médica assumir conversas e devolver para a IA.
    """

    @staticmethod
    async def create_ticket(
        db: AsyncSession,
        patient_id: int,
        reason: str = "Solicitação de atendimento humano"
    ) -> SupportTicket:
        patient = await PatientService.get_by_id(db, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")

        ticket = SupportTicket(
            patient_id=patient_id,
            status=TicketStatus.ABERTO_IA,
            reason=reason
        )
        db.add(ticket)
        await db.flush()

        patient.active_ticket_id = str(ticket.id)
        await db.flush()

        await ws_manager.broadcast({
            "type": "ticket_created",
            "ticket_id": ticket.id,
            "patient_id": patient_id,
            "patient_name": patient.name,
            "status": ticket.status.value
        })

        return ticket

    @staticmethod
    async def takeover_ticket(
        db: AsyncSession,
        ticket_id: int,
        agent_name: str
    ) -> SupportTicket:
        """Humano assume a conversa. IA pausa respostas automáticas."""
        result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket não encontrado")

        ticket.status = TicketStatus.ASSUMIDO_HUMANO
        ticket.assigned_agent = agent_name
        await db.flush()

        await ws_manager.broadcast({
            "type": "ticket_takeover",
            "ticket_id": ticket.id,
            "patient_id": ticket.patient_id,
            "agent_name": agent_name,
            "status": ticket.status.value
        })

        return ticket

    @staticmethod
    async def release_ticket(
        db: AsyncSession,
        ticket_id: int
    ) -> SupportTicket:
        """Humano devolve a conversa. IA reassume a orquestração automática."""
        result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket não encontrado")

        ticket.status = TicketStatus.ENCERRADO
        ticket.closed_at = datetime.now(timezone.utc)

        patient = await PatientService.get_by_id(db, ticket.patient_id)
        if patient:
            patient.active_ticket_id = None

        await db.flush()

        await ws_manager.broadcast({
            "type": "ticket_released",
            "ticket_id": ticket.id,
            "patient_id": ticket.patient_id,
            "status": "encerrado"
        })

        return ticket

    @staticmethod
    async def get_active_tickets(db: AsyncSession) -> List[SupportTicket]:
        result = await db.execute(
            select(SupportTicket)
            .where(SupportTicket.status != TicketStatus.ENCERRADO)
            .order_by(SupportTicket.created_at.desc())
        )
        return list(result.scalars().all())
