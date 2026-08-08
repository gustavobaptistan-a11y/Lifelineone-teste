from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.events import SystemEventPayload, EventProcessingResponse
from app.services.event_bus import event_bus

router = APIRouter()

@router.post("/publish", response_model=EventProcessingResponse)
async def publish_event(
    payload: SystemEventPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Publica um evento do sistema (ex: consulta_realizada, exame_disponivel, paciente_inativo_180_dias, pagamento_confirmado).
    O barramento de eventos executa as automações da jornada do paciente.
    """
    result = await event_bus.publish(
        db=db,
        event_type=payload.event_type,
        patient_id=payload.patient_id,
        data=payload.data
    )
    return result
