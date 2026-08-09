import uuid
import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    status = Column(String(50), default="em_andamento")
    current_goal = Column(String(255), nullable=True)
    is_ai_paused = Column(Boolean, default=False)
    is_human_handover_requested = Column(Boolean, default=False)
    handover_reason = Column(String(255), nullable=True)
    pre_consultation_summary = Column(String, nullable=True)
    pre_consultation_status = Column(String(50), default="pendente")
    started_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String(50), nullable=False)
    content = Column(String, nullable=False)
    message_type = Column(String(50), default="texto")
    media_url = Column(String(500), nullable=True)
    agent_name = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class AIAgentsLog(Base):
    __tablename__ = "ai_agents_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
