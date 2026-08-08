from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.analytics import FunnelAnalyticsResponse, AIPerformanceAnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/funnel", response_model=FunnelAnalyticsResponse)
async def get_funnel_analytics(db: AsyncSession = Depends(get_db)):
    """
    Retorna a análise de conversão do funil de jornada do paciente em tempo real.
    """
    return await AnalyticsService.get_funnel_metrics(db)

@router.get("/ai-performance", response_model=AIPerformanceAnalyticsResponse)
async def get_ai_performance_analytics(db: AsyncSession = Depends(get_db)):
    """
    Retorna métricas de performance do Lifeline AI Orchestrator (mensagens, intenções e ferramentas disparadas).
    """
    return await AnalyticsService.get_ai_performance_metrics(db)
