import uuid
from typing import Dict, Any, List, Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession

HandlerType = Callable[[AsyncSession, int, Dict[str, Any]], Awaitable[Dict[str, Any]]]

class EventBus:
    """
    Barramento de Eventos da Plataforma Lifeline One.
    Permite publicação de eventos do sistema e disparo de reações automáticas da IA e do sistema.
    """

    def __init__(self):
        self._handlers: Dict[str, List[HandlerType]] = {}

    def register(self, event_type: str, handler: HandlerType):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(
        self,
        db: AsyncSession,
        event_type: str,
        patient_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        event_id = str(uuid.uuid4())
        actions_triggered = []
        new_stage = None

        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                result = await handler(db, patient_id, data)
                if "action" in result:
                    actions_triggered.append(result["action"])
                if "new_stage" in result:
                    new_stage = result["new_stage"]

        return {
            "event_id": event_id,
            "event_type": event_type,
            "patient_id": patient_id,
            "actions_triggered": actions_triggered,
            "new_stage": new_stage
        }

event_bus = EventBus()
