import uuid
import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    cpf = Column(String(14), nullable=True)
    data_nascimento = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    telefone = Column(String(30), nullable=False, index=True)
    tipo_contato = Column(String(50), default="proprio")
    preferencias_comunicacao = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class PatientContact(Base):
    __tablename__ = "patient_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    parentesco = Column(String(50), default="proprio")
    responsavel_principal = Column(Boolean, default=True)
    permissao = Column(String(50), default="proprio")
