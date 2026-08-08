from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient import Patient
from app.models.journey import JourneyStage
from app.models.appointments import Appointment, AppointmentStatus
from app.services.patient_service import PatientService
from app.services.journey_service import JourneyService

class PlatformToolsService:
    """
    Conjunto de ferramentas (Tools) executáveis pela plataforma quando chamadas pela IA.
    A IA não inventa dados; ela consulta e executa ações reais no sistema.
    """

    @staticmethod
    async def consultar_agenda(
        db: AsyncSession,
        doctor_name: Optional[str] = None,
        specialty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # Exemplo de consulta de horários disponíveis na agenda médica
        slots = [
            {"doctor": doctor_name or "Dr. Luiz", "specialty": specialty or "Pneumologia", "date": "2026-08-10T09:00:00"},
            {"doctor": doctor_name or "Dr. Luiz", "specialty": specialty or "Pneumologia", "date": "2026-08-10T14:30:00"},
            {"doctor": "Dra. Maria", "specialty": "Cardiologia", "date": "2026-08-11T10:00:00"}
        ]
        if specialty:
            slots = [s for s in slots if specialty.lower() in s["specialty"].lower()]
        return slots

    @staticmethod
    async def criar_agendamento(
        db: AsyncSession,
        patient_id: int,
        doctor_name: str,
        specialty: str,
        appointment_date: str
    ) -> Dict[str, Any]:
        dt = datetime.fromisoformat(appointment_date)
        appointment = Appointment(
            patient_id=patient_id,
            doctor_name=doctor_name,
            specialty=specialty,
            appointment_date=dt,
            status=AppointmentStatus.AGENDADO
        )
        db.add(appointment)
        await db.flush()

        # Atualiza a jornada do paciente para 'agendamento'
        await JourneyService.transition_stage(
            db=db,
            patient_id=patient_id,
            to_stage=JourneyStage.AGENDAMENTO,
            trigger_event="tool_criar_agendamento",
            notes=f"Agendado com {doctor_name} para {appointment_date}"
        )

        return {
            "appointment_id": appointment.id,
            "patient_id": patient_id,
            "doctor": doctor_name,
            "specialty": specialty,
            "date": appointment_date,
            "status": "agendado"
        }

    @staticmethod
    async def reagendar_consulta(
        db: AsyncSession,
        appointment_id: int,
        new_date: str
    ) -> Dict[str, Any]:
        result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        appt = result.scalar_one_or_none()
        if not appt:
            return {"error": "Consulta não encontrada"}

        dt = datetime.fromisoformat(new_date)
        appt.appointment_date = dt
        appt.status = AppointmentStatus.REAGENDADO
        await db.flush()

        return {
            "appointment_id": appointment_id,
            "new_date": new_date,
            "status": "reagendado"
        }

    @staticmethod
    async def cancelar_consulta(
        db: AsyncSession,
        appointment_id: int,
        reason: str
    ) -> Dict[str, Any]:
        result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        appt = result.scalar_one_or_none()
        if not appt:
            return {"error": "Consulta não encontrada"}

        appt.status = AppointmentStatus.CANCELADO
        appt.notes = f"Motivo do cancelamento: {reason}"
        await db.flush()

        return {
            "appointment_id": appointment_id,
            "status": "cancelado",
            "reason": reason
        }

    @staticmethod
    async def consultar_convenios(db: AsyncSession) -> List[str]:
        return ["GEAP", "Unimed", "Bradesco Saúde", "SulAmérica", "Particular"]

    @staticmethod
    async def consultar_especialidades(db: AsyncSession) -> List[str]:
        return ["Pneumologia", "Cardiologia", "Dermatologia", "Pediatria", "Ortopedia", "Clínica Geral"]

    @staticmethod
    async def enviar_localizacao(db: AsyncSession, unit_name: str = "Unidade Central") -> Dict[str, str]:
        return {
            "unit": unit_name,
            "address": "Av. Paulista, 1000 - Bela Vista, São Paulo - SP",
            "maps_link": "https://maps.google.com/?q=Av+Paulista+1000"
        }

    @staticmethod
    async def criar_followup(
        db: AsyncSession,
        patient_id: int,
        description: str,
        scheduled_date: Optional[str] = None
    ) -> Dict[str, Any]:
        patient = await PatientService.get_by_id(db, patient_id)
        if not patient:
            return {"error": "Paciente não encontrado"}

        tasks = list(patient.pending_tasks or [])
        new_task = {
            "id": len(tasks) + 1,
            "description": description,
            "scheduled_date": scheduled_date or datetime.now(timezone.utc).isoformat(),
            "status": "pendente"
        }
        tasks.append(new_task)
        patient.pending_tasks = tasks
        await db.flush()

        return {
            "patient_id": patient_id,
            "task": new_task
        }
