from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.patient_service import PatientService
from app.services.journey_service import JourneyService
from app.services.ai_orchestrator import LifelineAIOrchestrator
from app.services.event_bus import event_bus
from app.services.exam_analysis_service import ExamAnalysisService
from app.models.journey import JourneyStage

router = APIRouter()

class FullJourneySimulationRequest(BaseModel):
    patient_name: str = "Gustavo Baptista (Teste E2E)"
    phone: str = "5511999998888"

@router.post("/full-journey")
async def run_full_patient_journey_simulation(
    payload: FullJourneySimulationRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Executa a simulação completa da Jornada do Paciente de Ponta a Ponta (End-to-End):
    1. Primeiro Contato no WhatsApp (Lead Criado / Pré-qualificação).
    2. Agendamento de Consulta via IA.
    3. Consulta Médica Realizada (Evento).
    4. Laboratório & Exames (Upload Espirometria + OCR Gemini).
    5. Tratamento Ativo & Confirmação de Pagamento.
    6. Consulta de Retorno & Alta Médica (Encerrado com Sucesso).
    7. Retorno da Visão Consolidada do PEP Unificado (Fonte da Verdade 360°).
    """
    steps_log = []

    # -----------------------------------------------------------------
    # ETAPA 1: Primeiro Contato no WhatsApp (Lead Criado)
    # -----------------------------------------------------------------
    msg1_res = await LifelineAIOrchestrator.process_incoming_message(
        db=db,
        phone=payload.phone,
        message_text="Olá, gostaria de agendar uma consulta com Pneumologista",
        patient_name=payload.patient_name
    )
    patient_id = msg1_res["patient_id"]
    steps_log.append({
        "step": "1. WhatsApp - Primeiro Contato",
        "stage": msg1_res["current_stage"],
        "intent": msg1_res["detected_intent"],
        "ai_response": msg1_res["ai_response"],
        "tools_executed": msg1_res["tools_executed"]
    })

    # -----------------------------------------------------------------
    # ETAPA 2: Agendamento Confirmado via IA
    # -----------------------------------------------------------------
    await JourneyService.transition_stage(
        db=db,
        patient_id=patient_id,
        to_stage=JourneyStage.AGENDAMENTO,
        trigger_event="agendamento_confirmado",
        notes="Consulta agendada para 15/08 às 14:00 com Dr. Carlos Pneumologia"
    )
    steps_log.append({
        "step": "2. Agendamento Confirmado",
        "stage": "agendamento",
        "details": "Consulta agendada com Dr. Carlos para 15/08 às 14:00"
    })

    # -----------------------------------------------------------------
    # ETAPA 3: Consulta Médica Realizada (Disparo de Evento)
    # -----------------------------------------------------------------
    ev_consulta = await event_bus.publish(
        db=db,
        event_type="consulta_realizada",
        patient_id=patient_id,
        data={"doctor": "Dr. Carlos Pneumologia", "notes": "Paciente com falta de ar. Solicitada espirometria."}
    )
    steps_log.append({
        "step": "3. Consulta Realizada",
        "stage": ev_consulta["new_stage"],
        "event": "consulta_realizada",
        "details": "Consulta concluída. Exame de Espirometria solicitado ao laboratório."
    })

    # -----------------------------------------------------------------
    # ETAPA 4: Laboratório & Exames (Upload Espirometria + OCR AI)
    # -----------------------------------------------------------------
    exam_res = await ExamAnalysisService.process_exam_upload(
        db=db,
        patient_id=patient_id,
        file_name="laudo_espirometria_gustavo.pdf",
        exam_type="Espirometria"
    )
    steps_log.append({
        "step": "4. Laboratório & Exames (OCR AI)",
        "stage": "exames",
        "exam_type": exam_res["exam_type"],
        "extracted_findings": exam_res["extracted_findings"],
        "details": "Laudo analisado pela IA e unificado no Prontuário (PEP)."
    })

    # -----------------------------------------------------------------
    # ETAPA 5: Tratamento Ativo & Pagamento Confirmado
    # -----------------------------------------------------------------
    ev_pagamento = await event_bus.publish(
        db=db,
        event_type="pagamento_confirmado",
        patient_id=patient_id,
        data={"amount": "R$ 450,00", "treatment_plan": "Inaloterapia + Broncodilatador 30 dias"}
    )
    steps_log.append({
        "step": "5. Tratamento Ativo & Pagamento",
        "stage": ev_pagamento["new_stage"],
        "event": "pagamento_confirmado",
        "details": "Plano terapêutico iniciado. Tratamento registrado no PEP."
    })

    # -----------------------------------------------------------------
    # ETAPA 6: Consulta de Retorno & Alta Médica
    # -----------------------------------------------------------------
    await JourneyService.transition_stage(
        db=db,
        patient_id=patient_id,
        to_stage=JourneyStage.RETORNO,
        trigger_event="consulta_retorno",
        notes="Retorno de avaliação pós-tratamento."
    )
    
    await JourneyService.transition_stage(
        db=db,
        patient_id=patient_id,
        to_stage=JourneyStage.ALTA,
        trigger_event="alta_medica",
        notes="Paciente assintomático. Concedida Alta Médica."
    )

    steps_log.append({
        "step": "6. Retorno & Alta Médica",
        "stage": "alta",
        "details": "Paciente obteve alta médica completa. Registrada no PEP Unificado."
    })

    # -----------------------------------------------------------------
    # ETAPA 7: Consulta da Fonte da Verdade (PEP Unificado 360°)
    # -----------------------------------------------------------------
    unified_pep = await PatientService.get_patient_state(db, str(patient_id))

    return {
        "status": "success",
        "simulation_message": "Jornada Completa do Paciente simulada de ponta a ponta!",
        "patient_id": patient_id,
        "journey_steps_executed": steps_log,
        "unified_pep_state": unified_pep
    }
