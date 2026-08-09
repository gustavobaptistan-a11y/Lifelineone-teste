from fastapi import APIRouter
from app.api.v1.endpoints import (
    patients, journey, orchestrator, events, webhooks, analytics,
    exams, websockets, tickets, simulation, lab_and_audit,
    auth, documents, patient_portal
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação & Controle de Acesso (RBAC/JWT)"])
api_router.include_router(patients.router, prefix="/patients", tags=["Estado do Paciente & CRM"])
api_router.include_router(journey.router, prefix="/journey", tags=["Jornada do Paciente"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["Lifeline AI Orchestrator"])
api_router.include_router(events.router, prefix="/events", tags=["Eventos do Sistema"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks & WhatsApp Integration"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Funil de Conversão"])
api_router.include_router(exams.router, prefix="/exams", tags=["Prontuário (PEP) & Análise de Exames"])
api_router.include_router(websockets.router, prefix="/ws", tags=["Transmissão WebSockets ao Vivo"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Atendimento Híbrido & Transbordo Humano"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["Simulador E2E da Jornada Completa"])
api_router.include_router(lab_and_audit.router, prefix="/lab-audit", tags=["Laboratório, Guardião de IA & Auditoria"])
api_router.include_router(documents.router, prefix="/documents", tags=["Gerador de Documentos Médicos PDF"])
api_router.include_router(patient_portal.router, prefix="/patient-portal", tags=["Portal do Paciente Mobile/Web"])
