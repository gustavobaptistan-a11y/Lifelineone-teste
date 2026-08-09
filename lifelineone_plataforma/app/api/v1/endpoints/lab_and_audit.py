from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lab_order import LabOrderStatus
from app.services.lab_workflow_service import LabWorkflowService
from app.services.integrity_guard_service import IntegrityGuardService
from app.services.journey_service import JourneyService
from app.models.journey import JourneyStage

router = APIRouter()

class CreateLabOrderRequest(BaseModel):
    patient_id: int
    exam_name: str = Field("Espirometria Completa", json_schema_extra={"example": "Espirometria"})
    requesting_doctor: str = Field("Dr. Carlos Pneumologia", json_schema_extra={"example": "Dr. Carlos"})
    unit_location: str = Field("Unidade Jardins - SP", json_schema_extra={"example": "Unidade Jardins - SP"})

class UpdateLabOrderStatusRequest(BaseModel):
    next_status: LabOrderStatus
    scheduled_date: Optional[str] = "16/08 às 09:00 (Coleta Domiciliar)"
    findings_summary: Optional[str] = "Padrão ventilatório normal sem limitações."
    actor_name: str = "Técnico Silva (Laboratório Central)"

class PostConsultationDecisionRequest(BaseModel):
    patient_id: int
    decision: str = Field("alta", json_schema_extra={"example": "alta"}) # alta ou novos_exames
    doctor_notes: str = Field("Paciente assintomático, laudos normais. Concedida Alta.", json_schema_extra={"example": "Alta concedida"})

@router.post("/orders")
async def create_lab_order(
    payload: CreateLabOrderRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Médico solicita exame de laboratório. Dispara automaticamente contato via WhatsApp pela IA.
    """
    order = await LabWorkflowService.create_lab_order(
        db=db,
        patient_id=payload.patient_id,
        exam_name=payload.exam_name,
        requesting_doctor=payload.requesting_doctor,
        unit_location=payload.unit_location
    )
    return {
        "status": "success",
        "lab_order_id": order.id,
        "current_stage": order.status.value,
        "whatsapp_notification": f"Contato disparado para o WhatsApp do paciente para agendamento de coleta."
    }

@router.post("/orders/{order_id}/status")
async def update_lab_order_status(
    order_id: int,
    payload: UpdateLabOrderStatusRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza os status de coleta/laboratório (Pedido ➔ Coleta ➔ Transporte ➔ Análise ➔ Liberado Cofre).
    """
    order = await LabWorkflowService.advance_lab_order_status(
        db=db,
        lab_order_id=order_id,
        next_status=payload.next_status,
        scheduled_date=payload.scheduled_date,
        findings_summary=payload.findings_summary,
        actor_name=payload.actor_name
    )
    return {
        "status": "success",
        "lab_order_id": order.id,
        "new_status": order.status.value,
        "vault_file_hash": order.vault_file_hash
    }

@router.get("/patient/{patient_id}")
async def get_patient_lab_orders(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna o rastreamento em tempo real de todos os pedidos de exames laboratoriais do paciente.
    """
    orders = await LabWorkflowService.get_patient_lab_orders(db, patient_id)
    return [
        {
            "id": o.id,
            "exam_name": o.exam_name,
            "requesting_doctor": o.requesting_doctor,
            "status": o.status.value,
            "unit": o.unit_location,
            "scheduled_date": o.scheduled_collection_date,
            "vault_hash": o.vault_file_hash,
            "findings": o.findings_summary,
            "created_at": o.created_at
        } for o in orders
    ]

@router.get("/audit/integrity/{patient_id}")
async def verify_pep_integrity_and_audit(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Guardião de IA: Audita 'Quem acessou', 'De onde acessou' e verifica integridade de segurança do PEP Master.
    """
    return await IntegrityGuardService.verify_pep_integrity(db, patient_id)

@router.post("/clinical-decision/post-consultation")
async def register_post_consultation_decision(
    payload: PostConsultationDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Decisão Médica Pós-Consulta (Avaliação dos Laudos): Alta Médica vs Solicitante de Novos Exames.
    """
    if payload.decision.lower() == "alta":
        await JourneyService.transition_stage(
            db=db,
            patient_id=payload.patient_id,
            to_stage=JourneyStage.ALTA,
            trigger_event="alta_medica_pos_exames",
            notes=payload.doctor_notes
        )
        msg = "Decisão registrada: Alta médica concedida e arquivada no PEP 360°."
    else:
        await JourneyService.transition_stage(
            db=db,
            patient_id=payload.patient_id,
            to_stage=JourneyStage.EXAMES,
            trigger_event="novos_exames_solicitados",
            notes=payload.doctor_notes
        )
        msg = "Decisão registrada: Ciclo de laboratório reiniciado para novos exames complementares."

    return {
        "status": "success",
        "patient_id": payload.patient_id,
        "decision": payload.decision,
        "message": msg
    }
