from typing import Dict, Any, List
from pydantic import BaseModel

class JourneyStageMetrics(BaseModel):
    stage: str
    label: str
    count: int
    conversion_rate_percentage: float

class FunnelAnalyticsResponse(BaseModel):
    total_patients: int
    stages_breakdown: List[JourneyStageMetrics]
    active_treatments_count: int
    pending_returns_count: int
    reactivated_count: int

class AIPerformanceAnalyticsResponse(BaseModel):
    total_messages_processed: int
    intents_breakdown: Dict[str, int]
    tools_execution_count: Dict[str, int]
