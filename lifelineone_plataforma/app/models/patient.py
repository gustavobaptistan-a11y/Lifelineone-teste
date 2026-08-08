from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, Integer, Boolean, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.journey import JourneyStage

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    birth_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Informações de Convênio
    insurance_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_card_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    insurance_plan: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Informações Médicas
    attending_doctor: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    doctor_crm: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    specialty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Estado da Jornada
    current_stage: Mapped[JourneyStage] = mapped_column(
        SQLEnum(JourneyStage), default=JourneyStage.LEAD_CRIADO, nullable=False
    )
    active_treatment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_return_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Pendências, Exames e Ticket
    pending_tasks: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    exams_data: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    active_ticket_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadados de interação
    last_interaction: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    current_intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamento com histórico de jornada
    journey_history: Mapped[List["JourneyHistory"]] = relationship(
        "JourneyHistory", back_populates="patient", cascade="all, delete-orphan"
    )
