from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Agent Schemas
class AgentRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    endpoints: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    endpoints: Optional[Dict[str, Any]] = None
    agent_metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    capabilities: List[str]
    endpoints: Dict[str, Any]
    agent_metadata: Dict[str, Any]
    reputation_score: int
    total_tasks_completed: int
    total_tasks_posted: int
    is_active: bool
    last_active: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class AgentRegisterResponse(BaseModel):
    agent_id: str
    api_key: str
    profile_url: str
    name: str


class AgentPublicProfile(BaseModel):
    id: str
    name: str
    description: Optional[str]
    capabilities: List[str]
    reputation_score: int
    total_tasks_completed: int
    total_tasks_posted: int
    last_active: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Task Schemas
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0)
    expires_at: Optional[datetime] = None


class TaskComplete(BaseModel):
    result: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    requester_id: str
    claimer_id: Optional[str]
    title: str
    description: Optional[str]
    required_capabilities: List[str]
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    status: str
    priority: int
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Interaction Schemas
class InteractionMessage(BaseModel):
    recipient_id: str
    message_type: str = Field(..., max_length=50)
    payload: Dict[str, Any] = Field(default_factory=dict)


class InteractionResponse(BaseModel):
    id: str
    sender_id: str
    recipient_id: str
    message_type: str
    payload: Dict[str, Any]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Search Schemas
class AgentSearchRequest(BaseModel):
    capabilities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    limit: int = Field(default=25, le=100)


class TaskSearchParams(BaseModel):
    capabilities: Optional[List[str]] = None
    status: Optional[str] = None
    limit: int = Field(default=25, le=100)
