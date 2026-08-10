import uuid
import datetime
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.calendar_service import calendar_service
from app.models.appointment import Doctor, Appointment

logger = logging.getLogger(__name__)


class SchedulerAgent:
    """
    Agente Agenda.
    Lida com consultas de horários, reservas, remarcações, busca de agendamento ativo e cancelamentos.
    """

    async def find_available_slots(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        target_date: Optional[datetime.date] = None,
        preferred_period: Optional[str] = None
    ) -> Dict[str, Any]:
        if not target_date:
            target_date = datetime.date.today() + datetime.timedelta(days=1)

        try:
            stmt = select(Doctor).where(Doctor.clinic_id == clinic_id, Doctor.status == "ativo")
            result = await db.execute(stmt)
            doctor = result.scalars().first()

            if not doctor:
                doctor = Doctor(
                    clinic_id=clinic_id,
                    nome="Dra. Ana Alergologista",
                    especialidade="Alergia e Imunologia Pediátrica e Adulto"
                )
                db.add(doctor)
                await db.flush()
                await db.refresh(doctor)
            
            doc_id = doctor.id
            doc_name = doctor.nome
            doc_esp = doctor.especialidade
        except Exception as e:
            await db.rollback()
            logger.info(f"Doctor fallback: {e}")
            doc_id = uuid.uuid4()
            doc_name = "Dra. Ana Alergologista"
            doc_esp = "Alergia e Imunologia Pediátrica e Adulto"

        slots = await calendar_service.get_available_slots(doc_id, target_date)
        all_times = [s["time"] for s in slots if s["available"]]

        if preferred_period == "tarde":
            afternoon = [t for t in all_times if int(t.split(":")[0]) >= 12]
            morning = [t for t in all_times if int(t.split(":")[0]) < 12]
            ordered_times = afternoon + morning
        elif preferred_period == "manha":
            morning = [t for t in all_times if int(t.split(":")[0]) < 12]
            afternoon = [t for t in all_times if int(t.split(":")[0]) >= 12]
            ordered_times = morning + afternoon
        else:
            ordered_times = all_times

        return {
            "doctor_id": str(doc_id),
            "doctor_name": doc_name,
            "especialidade": doc_esp,
            "data": target_date.strftime("%d/%m/%Y"),
            "horarios_disponiveis": ordered_times
        }

    async def create_booking(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        date_time: datetime.datetime,
        tipo_consulta: str = "primeira_consulta"
    ) -> Appointment | None:
        gcal_res = await calendar_service.create_event(
            doctor_id=doctor_id,
            patient_name="Paciente",
            start_time=date_time,
            summary=f"Consulta de Alergia - {tipo_consulta}"
        )

        try:
            appointment = Appointment(
                clinic_id=clinic_id,
                patient_id=patient_id,
                doctor_id=doctor_id,
                calendar_event_id=gcal_res["calendar_event_id"],
                tipo_consulta=tipo_consulta,
                data_hora=date_time,
                status="reservado"
            )
            db.add(appointment)
            await db.flush()
            return appointment
        except Exception as e:
            await db.rollback()
            logger.info(f"Booking não persistido: {e}")
            return None

    async def get_active_patient_booking(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        patient_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Busca se o paciente possui um agendamento ativo recente/futuro."""
        try:
            stmt = select(Appointment).where(
                Appointment.clinic_id == clinic_id,
                Appointment.patient_id == patient_id,
                Appointment.status.in_(["reservado", "confirmado", "agendado"])
            ).order_by(Appointment.data_hora.desc())
            res = await db.execute(stmt)
            apt = res.scalars().first()
            if apt and apt.data_hora:
                return {
                    "appointment_id": str(apt.id),
                    "data_hora_str": apt.data_hora.strftime("%d/%m/%Y às %H:%M"),
                    "data": apt.data_hora.strftime("%d/%m/%Y"),
                    "horario": apt.data_hora.strftime("%H:%M")
                }
        except Exception as e:
            logger.info(f"Sem agendamento ativo DB: {e}")
        return None


scheduler_agent = SchedulerAgent()
