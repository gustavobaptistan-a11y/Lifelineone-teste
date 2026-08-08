import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient import Patient
from app.services.event_bus import event_bus

class BackgroundSchedulerService:
    """
    Serviço de agendamento em segundo plano.
    Monitora periodicamente a base de dados para automações de jornada (ex: inatividade de 180 dias).
    """

    @staticmethod
    async def check_inactive_patients(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Busca pacientes sem interação há mais de 180 dias e dispara o evento 'paciente_inativo_180_dias'.
        """
        limit_date = datetime.now(timezone.utc) - timedelta(days=180)
        
        result = await db.execute(
            select(Patient).where(Patient.last_interaction <= limit_date)
        )
        inactive_patients = list(result.scalars().all())

        events_dispatched = []
        for patient in inactive_patients:
            res = await event_bus.publish(
                db=db,
                event_type="paciente_inativo_180_dias",
                patient_id=patient.id,
                data={"days_inactive": 180}
            )
            events_dispatched.append(res)

        return events_dispatched

scheduler_service = BackgroundSchedulerService()
