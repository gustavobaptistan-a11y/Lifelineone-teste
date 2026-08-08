import uuid
import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_fantasia = Column(String(255), nullable=True)
    cnpj = Column(String(20), nullable=True)
    plano = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True, default="ativo")
    configuracoes = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
