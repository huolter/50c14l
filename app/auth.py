from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import Agent
import secrets
import bcrypt

security = HTTPBearer()


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    # Truncate to 72 bytes if needed (bcrypt limitation)
    api_key_bytes = api_key.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(api_key_bytes, salt)
    return hashed.decode('utf-8')


def verify_api_key_hash(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    plain_key_bytes = plain_key.encode('utf-8')[:72]
    hashed_bytes = hashed_key.encode('utf-8')
    return bcrypt.checkpw(plain_key_bytes, hashed_bytes)


def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> Agent:
    """
    Dependency to get the current authenticated agent from API key.
    """
    api_key = credentials.credentials

    # Query all agents and check their hashed keys
    # Note: This is not the most efficient for large scale, but works for our use case
    agents = db.query(Agent).filter(Agent.is_active == True).all()

    for agent in agents:
        if verify_api_key_hash(api_key, agent.api_key_hash):
            return agent

    raise HTTPException(
        status_code=401,
        detail="Invalid API key"
    )
