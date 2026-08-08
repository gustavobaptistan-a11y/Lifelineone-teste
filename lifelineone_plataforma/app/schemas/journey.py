from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.journey import JourneyStage

class JourneyTransitionCreate(BaseModel):
    to_stage: JourneyStage
    trigger_event: str = "manual_update"
    notes: Optional[str] = None

class JourneyHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    from_stage: Optional[JourneyStage]
    to_stage: JourneyStage
    trigger_event: str
    notes: Optional[str]
    created_at: datetime
