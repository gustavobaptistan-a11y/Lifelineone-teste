from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.patient import Patient
from app.models.journey import JourneyStage
from app.models.conversation import ConversationMessage
from app.schemas.analytics import FunnelAnalyticsResponse, JourneyStageMetrics, AIPerformanceAnalyticsResponse

STAGE_LABELS = {
    JourneyStage.LEAD_CRIADO: "Lead Criado",
    JourneyStage.PRIMEIRO_CONTATO: "Primeiro Contato",
    JourneyStage.PRE_QUALIFICACAO: "Pré-qualificação",
    JourneyStage.AGENDAMENTO: "Agendamento",
    JourneyStage.CONSULTA_REALIZADA: "Consulta Realizada",
    JourneyStage.EXAMES: "Exames",
    JourneyStage.TRATAMENTO: "Tratamento",
    JourneyStage.RETORNO: "Retorno",
    JourneyStage.ALTA: "Alta",
    JourneyStage.REATIVACAO: "Reativação (180d)"
}

class AnalyticsService:
    """
    Serviço de análise de métricas e performance do funil de jornada e da IA.
    """

    @staticmethod
    async def get_funnel_metrics(db: AsyncSession) -> FunnelAnalyticsResponse:
        # Total de pacientes
        total_res = await db.execute(select(func.count(Patient.id)))
        total_patients = total_res.scalar() or 0

        # Contagem por etapa
        breakdown: List[JourneyStageMetrics] = []
        for stage in JourneyStage:
            cnt_res = await db.execute(select(func.count(Patient.id)).where(Patient.current_stage == stage))
            cnt = cnt_res.scalar() or 0
            rate = round((cnt / total_patients * 100), 2) if total_patients > 0 else 0.0
            breakdown.append(
                JourneyStageMetrics(
                    stage=stage.value,
                    label=STAGE_LABELS.get(stage, stage.value),
                    count=cnt,
                    conversion_rate_percentage=rate
                )
            )

        # Contagens específicas
        active_treat_res = await db.execute(select(func.count(Patient.id)).where(Patient.active_treatment.isnot(None)))
        active_treatments_count = active_treat_res.scalar() or 0

        pending_ret_res = await db.execute(select(func.count(Patient.id)).where(Patient.expected_return_date.isnot(None)))
        pending_returns_count = pending_ret_res.scalar() or 0

        reactivated_res = await db.execute(select(func.count(Patient.id)).where(Patient.current_stage == JourneyStage.REATIVACAO))
        reactivated_count = reactivated_res.scalar() or 0

        return FunnelAnalyticsResponse(
            total_patients=total_patients,
            stages_breakdown=breakdown,
            active_treatments_count=active_treatments_count,
            pending_returns_count=pending_returns_count,
            reactivated_count=reactivated_count
        )

    @staticmethod
    async def get_ai_performance_metrics(db: AsyncSession) -> AIPerformanceAnalyticsResponse:
        msg_cnt_res = await db.execute(select(func.count(ConversationMessage.id)))
        total_messages = msg_cnt_res.scalar() or 0

        # Intenções detectadas
        intents_res = await db.execute(
            select(Patient.current_intent, func.count(Patient.id))
            .where(Patient.current_intent.isnot(None))
            .group_by(Patient.current_intent)
        )
        intents_breakdown = {intent: count for intent, count in intents_res.all()}

        # Simulação de estatísticas de execução de ferramentas
        tools_execution = {
            "consultar_agenda": 15,
            "consultar_convenios": 12,
            "enviar_localizacao": 8,
            "criar_agendamento": 6,
            "criar_followup": 10
        }

        return AIPerformanceAnalyticsResponse(
            total_messages_processed=total_messages,
            intents_breakdown=intents_breakdown,
            tools_execution_count=tools_execution
        )
