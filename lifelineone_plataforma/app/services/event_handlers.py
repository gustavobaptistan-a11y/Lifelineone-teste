from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journey import JourneyStage
from app.models.conversation import ConversationMessage
from app.services.journey_service import JourneyService
from app.services.patient_service import PatientService
from app.services.tools_service import PlatformToolsService
from app.services.event_bus import event_bus

async def handle_consulta_realizada(
    db: AsyncSession,
    patient_id: int,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evento: Consulta realizada.
    Fluxo do PDF (pág 5):
    Consulta realizada -> Atualizar jornada -> Criar retorno -> Programar lembrete -> Criar follow-up
    """
    # 1. Atualizar Jornada
    await JourneyService.transition_stage(
        db=db,
        patient_id=patient_id,
        to_stage=JourneyStage.CONSULTA_REALIZADA,
        trigger_event="evento_consulta_realizada",
        notes=f"Consulta realizada com {data.get('doctor', 'Médico')}. Diagnóstico: {data.get('notes', 'Sem observações')}"
    )

    # 2. Criar Follow-up / Lembrete de retorno
    task_res = await PlatformToolsService.criar_followup(
        db=db,
        patient_id=patient_id,
        description=f"Lembrete de retorno pós-consulta ({data.get('doctor', 'Médico')})",
        scheduled_date=data.get("return_date")
    )

    return {
        "action": "jornada_atualizada_e_followup_criado",
        "new_stage": JourneyStage.CONSULTA_REALIZADA.value,
        "details": task_res
    }

async def handle_exame_disponivel(
    db: AsyncSession,
    patient_id: int,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evento: Exame disponível.
    Fluxo do PDF (pág 5-6):
    Exame disponível -> Notificar paciente -> Oferecer agendamento
    """
    exam_name = data.get("exam_name", "Exame sem nome")
    patient = await PatientService.get_by_id(db, patient_id)
    
    if patient:
        # Atualiza a jornada para 'exames'
        await JourneyService.transition_stage(
            db=db,
            patient_id=patient_id,
            to_stage=JourneyStage.EXAMES,
            trigger_event="evento_exame_disponivel",
            notes=f"Exame '{exam_name}' disponível no portal"
        )

        # Simula o envio de notificação automática via WhatsApp
        notify_msg = ConversationMessage(
            patient_id=patient_id,
            sender="sistema",
            content=f"Olá {patient.name}! Seu exame '{exam_name}' já está disponível. Gostaria de agendar o retorno médico?"
        )
        db.add(notify_msg)
        await db.flush()

    return {
        "action": "notificacao_exame_enviada",
        "new_stage": JourneyStage.EXAMES.value,
        "exam": exam_name
    }

async def handle_paciente_inativo_180_dias(
    db: AsyncSession,
    patient_id: int,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evento: Paciente não retorna há 180 dias.
    Fluxo do PDF (pág 6):
    Paciente inativo há 180 dias -> Criar fluxo de reativação
    """
    await JourneyService.transition_stage(
        db=db,
        patient_id=patient_id,
        to_stage=JourneyStage.REATIVACAO,
        trigger_event="evento_inativo_180_dias",
        notes="Paciente inativo há mais de 180 dias. Fluxo de reativação iniciado."
    )

    await PlatformToolsService.criar_followup(
        db=db,
        patient_id=patient_id,
        description="Campanha de reativação automatizada - Contato de check-up de saúde"
    )

    return {
        "action": "fluxo_reativacao_iniciado",
        "new_stage": JourneyStage.REATIVACAO.value
    }

async def handle_pagamento_confirmado(
    db: AsyncSession,
    patient_id: int,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evento: Pagamento confirmado.
    Fluxo do PDF (pág 6):
    Pagamento confirmado -> Liberar próxima etapa
    """
    await JourneyService.transition_stage(
        db=db,
        patient_id=patient_id,
        to_stage=JourneyStage.TRATAMENTO,
        trigger_event="evento_pagamento_confirmado",
        notes=f"Pagamento confirmado ({data.get('amount', 'R$ 0')}). Próxima etapa liberada."
    )

    return {
        "action": "proxima_etapa_liberada",
        "new_stage": JourneyStage.TRATAMENTO.value
    }

def setup_event_handlers():
    """Registra todos os handlers no barramento de eventos."""
    event_bus.register("consulta_realizada", handle_consulta_realizada)
    event_bus.register("exame_disponivel", handle_exame_disponivel)
    event_bus.register("paciente_inativo_180_dias", handle_paciente_inativo_180_dias)
    event_bus.register("pagamento_confirmado", handle_pagamento_confirmado)
