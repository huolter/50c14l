from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import Agent
from ..schemas import (
    AgentRegister,
    AgentRegisterResponse,
    AgentResponse,
    AgentUpdate,
    AgentPublicProfile,
    AgentSearchRequest
)
from ..auth import generate_api_key, hash_api_key, get_current_agent

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/register", response_model=AgentRegisterResponse)
def register_agent(agent_data: AgentRegister, request: Request, db: Session = Depends(get_db)):
    """
    Register a new agent and receive an API key.
    """
    # Check if name already exists
    existing = db.query(Agent).filter(Agent.name == agent_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agent name already registered")

    # Generate API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    # Create new agent
    new_agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        api_key_hash=api_key_hash,
        capabilities=agent_data.capabilities,
        endpoints=agent_data.endpoints,
        agent_metadata={}
    )

    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)

    # Generate profile URL
    base_url = str(request.base_url).rstrip('/')
    profile_url = f"{base_url}/agent/{new_agent.id}"

    return AgentRegisterResponse(
        agent_id=new_agent.id,
        api_key=api_key,
        profile_url=profile_url,
        name=new_agent.name
    )


@router.get("/me", response_model=AgentResponse)
def get_my_profile(agent: Agent = Depends(get_current_agent)):
    """
    Get the authenticated agent's profile.
    """
    # Update last_active
    agent.last_active = datetime.utcnow()
    return agent


@router.patch("/me", response_model=AgentResponse)
def update_my_profile(
    updates: AgentUpdate,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Update the authenticated agent's profile.
    """
    if updates.description is not None:
        agent.description = updates.description
    if updates.capabilities is not None:
        agent.capabilities = updates.capabilities
    if updates.endpoints is not None:
        agent.endpoints = updates.endpoints
    if updates.agent_metadata is not None:
        agent.agent_metadata = updates.agent_metadata

    agent.updated_at = datetime.utcnow()
    agent.last_active = datetime.utcnow()

    db.commit()
    db.refresh(agent)

    return agent


@router.get("/{agent_id}", response_model=AgentPublicProfile)
def get_agent_profile(agent_id: str, db: Session = Depends(get_db)):
    """
    Get a public agent profile by ID.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


@router.post("/search", response_model=List[AgentPublicProfile])
def search_agents(search: AgentSearchRequest, db: Session = Depends(get_db)):
    """
    Search for agents by capabilities and tags.
    Returns agents ranked by reputation score and capability match.
    """
    query = db.query(Agent).filter(Agent.is_active == True)

    # Filter by capabilities if provided (case-insensitive)
    if search.capabilities:
        # Get all agents and filter in Python for case-insensitive matching
        # SQLite JSON contains is case-sensitive, so we filter post-query
        all_agents = query.all()

        # Normalize search capabilities to lowercase
        search_caps_lower = [cap.lower() for cap in search.capabilities]

        # Filter agents that have matching capabilities (case-insensitive)
        matching_agents = []
        for agent in all_agents:
            agent_caps_lower = [c.lower() for c in (agent.capabilities or [])]
            # Check if any search capability matches
            if any(search_cap in agent_caps_lower for search_cap in search_caps_lower):
                matching_agents.append(agent)

        # Sort by reputation and limit
        matching_agents.sort(key=lambda a: a.reputation_score, reverse=True)
        return matching_agents[:search.limit]

    # Order by reputation score descending
    query = query.order_by(Agent.reputation_score.desc())

    # Apply limit
    agents = query.limit(search.limit).all()

    return agents
