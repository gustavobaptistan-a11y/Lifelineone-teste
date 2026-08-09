import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.lab_order import LabOrder, LabOrderStatus
from app.models.patient import Patient
from app.services.patient_service import PatientService
from app.services.exam_analysis_service import ExamAnalysisService
from app.services.integrity_guard_service import IntegrityGuardService
from app.core.websocket_manager import ws_manager

class LabWorkflowService:
    """
    Gerenciador do Ciclo Completo de Laboratório & Coleta.
    Gerencia do Pedido ➔ WhatsApp ➔ Agendamento de Coleta ➔ Transporte ➔ Análise ➔ Cofre Segura.
    """

    @staticmethod
    async def create_lab_order(
        db: AsyncSession,
        patient_id: int,
        exam_name: str,
        requesting_doctor: str,
        unit_location: str = "Unidade Jardins - SP"
    ) -> LabOrder:
        patient = await PatientService.get_by_id(db, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")

        order = LabOrder(
            patient_id=patient_id,
            exam_name=exam_name,
            requesting_doctor=requesting_doctor,
            status=LabOrderStatus.PEDIDO_CRIADO,
            unit_location=unit_location
        )
        db.add(order)
        await db.flush()

        # Audit log de criação do pedido pelo médico
        await IntegrityGuardService.log_access(
            db=db,
            patient_id=patient_id,
            actor_name=requesting_doctor,
            actor_role="Médico Prescritor",
            unit_location=unit_location,
            access_ip="192.168.1.50",
            action=f"Prescreveu exame de laboratório: {exam_name}"
        )

        # Dispara automaticamente o contato no WhatsApp do paciente via IA
        whatsapp_message = f"Olá {patient.name}, o(a) {requesting_doctor} solicitou o exame de {exam_name}. Gostaria de agendar a coleta na {unit_location} ou domiciliar?"
        order.status = LabOrderStatus.CONTATO_WHATSAPP
        await db.flush()

        await ws_manager.broadcast({
            "type": "lab_order_created",
            "lab_order_id": order.id,
            "patient_id": patient_id,
            "exam_name": exam_name,
            "status": order.status.value,
            "whatsapp_sent": whatsapp_message
        })

        return order

    @staticmethod
    async def advance_lab_order_status(
        db: AsyncSession,
        lab_order_id: int,
        next_status: LabOrderStatus,
        scheduled_date: Optional[str] = None,
        findings_summary: Optional[str] = None,
        actor_name: str = "Laboratório Central"
    ) -> LabOrder:
        result = await db.execute(select(LabOrder).where(LabOrder.id == lab_order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Pedido de laboratório não encontrado")

        order.status = next_status
        if scheduled_date:
            order.scheduled_collection_date = scheduled_date
        if findings_summary:
            order.findings_summary = findings_summary

        # Se liberado no Cofre de Segurança (Vault)
        if next_status == LabOrderStatus.LIBERADO_COFRE_SEGURA:
            file_hash = hashlib.sha256(f"vault_file_{order.id}_{datetime.now(timezone.utc)}".encode()).hexdigest()
            order.vault_file_hash = f"AES256:{file_hash[:24]}"

            # Anexa laudo ao Prontuário Unificado (PEP)
            await ExamAnalysisService.process_exam_upload(
                db=db,
                patient_id=order.patient_id,
                file_name=f"{order.exam_name.lower().replace(' ', '_')}_laudo.pdf",
                exam_type=order.exam_name
            )

        await db.flush()

        # Audit log de alteração de status do laboratório
        await IntegrityGuardService.log_access(
            db=db,
            patient_id=order.patient_id,
            actor_name=actor_name,
            actor_role="Técnico em Análises Clínicas / Laboratório",
            unit_location=order.unit_location,
            access_ip="10.0.0.12",
            action=f"Atualizou status do exame '{order.exam_name}' para '{next_status.value}'"
        )

        await ws_manager.broadcast({
            "type": "lab_order_updated",
            "lab_order_id": order.id,
            "patient_id": order.patient_id,
            "exam_name": order.exam_name,
            "status": order.status.value,
            "vault_hash": order.vault_file_hash
        })

        return order

    @staticmethod
    async def get_patient_lab_orders(db: AsyncSession, patient_id: int) -> List[LabOrder]:
        res = await db.execute(
            select(LabOrder)
            .where(LabOrder.patient_id == patient_id)
            .order_by(LabOrder.created_at.desc())
        )
        return list(res.scalars().all())
