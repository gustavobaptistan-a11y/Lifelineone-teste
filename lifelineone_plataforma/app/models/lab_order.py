import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class LabOrderStatus(str, enum.Enum):
    PEDIDO_CRIADO = "pedido_criado"
    CONTATO_WHATSAPP = "contato_whatsapp"
    COLETA_AGENDADA = "coleta_agendada"
    EM_TRANSPORTE = "em_transporte"
    ANALISE_LABORATORIAL = "analise_laboratorial"
    LIBERADO_COFRE_SEGURA = "liberado_cofre_segura"

class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    exam_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requesting_doctor: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[LabOrderStatus] = mapped_column(Enum(LabOrderStatus), default=LabOrderStatus.PEDIDO_CRIADO, nullable=False)
    unit_location: Mapped[str] = mapped_column(String(150), default="Unidade Jardins - SP")
    scheduled_collection_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vault_file_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    findings_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    patient: Mapped["Patient"] = relationship("Patient")
