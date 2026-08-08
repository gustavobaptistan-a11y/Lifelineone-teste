from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.journey import JourneyTransitionCreate, JourneyHistoryResponse
from app.schemas.patient import PatientStateResponse
from app.services.journey_service import JourneyService
from app.services.patient_service import PatientService

router = APIRouter()

@router.post("/{patient_id}/transition", response_model=PatientStateResponse)
async def transition_journey_stage(
    patient_id: int,
    transition_in: JourneyTransitionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Realiza a transição de etapa da Jornada do Paciente e grava a entrada de histórico.
    Retorna o Estado do Paciente atualizado.
    """
    await JourneyService.transition_stage(
        db=db,
        patient_id=patient_id,
        to_stage=transition_in.to_stage,
        trigger_event=transition_in.trigger_event,
        notes=transition_in.notes
    )
    return await PatientService.get_patient_state(db, str(patient_id))

@router.get("/{patient_id}/history", response_model=List[JourneyHistoryResponse])
async def get_journey_history(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna todo o histórico de transições de jornada de um determinado paciente.
    """
    return await JourneyService.get_journey_history(db, patient_id)
