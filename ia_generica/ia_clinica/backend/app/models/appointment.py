import uuid
import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    especialidade = Column(String(255), nullable=True)
    status = Column(String(50), default="ativo")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    calendar_event_id = Column(String(255), nullable=True)
    tipo_consulta = Column(String(100), default="primeira_consulta")
    data_hora = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="reservado")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
