from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class SystemEventPayload(BaseModel):
    event_type: str = Field(..., json_schema_extra={"example": "consulta_realizada"})
    patient_id: int = Field(..., json_schema_extra={"example": 1})
    data: Dict[str, Any] = Field(default_factory=dict, json_schema_extra={"example": {"doctor": "Dr. Luiz", "notes": "Rinite"}})

class EventProcessingResponse(BaseModel):
    event_id: str
    event_type: str
    patient_id: int
    actions_triggered: list
    new_stage: Optional[str] = None
