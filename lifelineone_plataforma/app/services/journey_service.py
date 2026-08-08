from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.patient import Patient
from app.models.journey import JourneyStage, JourneyHistory

class JourneyService:
    @staticmethod
    async def transition_stage(
        db: AsyncSession,
        patient_id: int,
        to_stage: JourneyStage,
        trigger_event: str = "manual_update",
        notes: Optional[str] = None
    ) -> JourneyHistory:
        result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")

        from_stage = patient.current_stage
        
        # Atualiza o estado atual do paciente
        patient.current_stage = to_stage
        patient.last_interaction = datetime.now(timezone.utc)

        # Grava a transição no histórico
        history_entry = JourneyHistory(
            patient_id=patient.id,
            from_stage=from_stage,
            to_stage=to_stage,
            trigger_event=trigger_event,
            notes=notes
        )

        db.add(history_entry)
        await db.flush()
        return history_entry

    @staticmethod
    async def get_journey_history(
        db: AsyncSession,
        patient_id: int
    ) -> List[JourneyHistory]:
        result = await db.execute(
            select(JourneyHistory)
            .where(JourneyHistory.patient_id == patient_id)
            .order_by(JourneyHistory.created_at.desc())
        )
        return list(result.scalars().all())
