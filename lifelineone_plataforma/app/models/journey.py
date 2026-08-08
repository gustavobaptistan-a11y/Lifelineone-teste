import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class JourneyStage(str, enum.Enum):
    LEAD_CRIADO = "lead_criado"
    PRIMEIRO_CONTATO = "primeiro_contato"
    PRE_QUALIFICACAO = "pre_qualificacao"
    AGENDAMENTO = "agendamento"
    CONSULTA_REALIZADA = "consulta_realizada"
    EXAMES = "exames"
    TRATAMENTO = "tratamento"
    RETORNO = "retorno"
    ALTA = "alta"
    REATIVACAO = "reativacao"

class JourneyHistory(Base):
    __tablename__ = "journey_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    from_stage: Mapped[Optional[JourneyStage]] = mapped_column(Enum(JourneyStage), nullable=True)
    to_stage: Mapped[JourneyStage] = mapped_column(Enum(JourneyStage), nullable=False)
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False, default="manual_update")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient: Mapped["Patient"] = relationship("Patient", back_populates="journey_history")
