from fastapi import APIRouter
from app.api.v1.endpoints import patients, journey, orchestrator, events

api_router = APIRouter()
api_router.include_router(patients.router, prefix="/patients", tags=["Estado do Paciente & CRM"])
api_router.include_router(journey.router, prefix="/journey", tags=["Jornada do Paciente"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["Lifeline AI Orchestrator"])
api_router.include_router(events.router, prefix="/events", tags=["Eventos do Sistema"])
