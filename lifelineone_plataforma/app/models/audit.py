from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(150), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(100), nullable=False) # Ex: "Médico", "Laboratório", "IA Guardiã", "Recepção"
    unit_location: Mapped[str] = mapped_column(String(150), nullable=False, default="Unidade Jardins - SP")
    access_ip: Mapped[str] = mapped_column(String(50), nullable=False, default="127.0.0.1")
    action: Mapped[str] = mapped_column(String(255), nullable=False) # Ex: "Visualizou PEP", "Prescreveu Espirometria"
    ai_integrity_status: Mapped[str] = mapped_column(String(50), default="VALIDO") # VALIDO / ANOMALIA_DETECTADA
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient: Mapped["Patient"] = relationship("Patient")
