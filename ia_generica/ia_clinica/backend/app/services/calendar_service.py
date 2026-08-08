import uuid
import datetime
from typing import List, Dict, Any


class CalendarService:
    """
    Serviço de Integração com Google Calendar e gestão de agenda médica.
    """

    async def get_available_slots(
        self,
        doctor_id: uuid.UUID,
        target_date: datetime.date
    ) -> List[Dict[str, Any]]:
        return [
            {"time": "08:00", "available": True},
            {"time": "09:00", "available": True},
            {"time": "10:00", "available": True},
            {"time": "14:00", "available": True},
            {"time": "15:30", "available": True}
        ]

    async def create_event(
        self,
        doctor_id: uuid.UUID,
        patient_name: str,
        start_time: datetime.datetime,
        summary: str = "Consulta Médica"
    ) -> Dict[str, Any]:
        event_id = f"gcal_{uuid.uuid4().hex[:12]}"
        return {
            "status": "created",
            "calendar_event_id": event_id,
            "start_time": start_time.isoformat(),
            "summary": summary
        }


calendar_service = CalendarService()
