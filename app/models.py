from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from .database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    api_key_hash = Column(String(255), unique=True, nullable=False)
    capabilities = Column(JSON, default=list)  # Store as JSON list
    endpoints = Column(JSON, default=dict)  # Store as JSON dict
    agent_metadata = Column(JSON, default=dict)  # Store as JSON dict (renamed from metadata)
    reputation_score = Column(Integer, default=0, index=True)
    total_tasks_completed = Column(Integer, default=0)
    total_tasks_posted = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    requester_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    claimer_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    required_capabilities = Column(JSON, default=list)  # Store as JSON list
    payload = Column(JSON, default=dict)  # Store as JSON dict
    result = Column(JSON, nullable=True)  # Store as JSON dict
    status = Column(String(20), default="open", index=True)  # open, in_progress, completed, cancelled
    priority = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    sender_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    message_type = Column(String(50))
    payload = Column(JSON)  # Store as JSON dict
    status = Column(String(20), default="sent")  # sent, delivered, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ReputationLog(Base):
    __tablename__ = "reputation_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50))
    value_change = Column(Integer)
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
