from fastapi import APIRouter
from app.api.v1.endpoints import patients, journey, orchestrator, events, webhooks, analytics, exams, websockets

api_router = APIRouter()
api_router.include_router(patients.router, prefix="/patients", tags=["Estado do Paciente & CRM"])
api_router.include_router(journey.router, prefix="/journey", tags=["Jornada do Paciente"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["Lifeline AI Orchestrator"])
api_router.include_router(events.router, prefix="/events", tags=["Eventos do Sistema"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks & WhatsApp Integration"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Funil de Conversão"])
api_router.include_router(exams.router, prefix="/exams", tags=["Prontuário (PEP) & Análise de Exames"])
api_router.include_router(websockets.router, prefix="/ws", tags=["Transmissão WebSockets ao Vivo"])
