from sqlalchemy.orm import Session
from datetime import datetime
from ..models import Agent, ReputationLog


def update_reputation(db: Session, agent_id: str, action: str, value_change: int, reason: str = ""):
    """
    Update an agent's reputation score and log the change.

    Args:
        db: Database session
        agent_id: ID of the agent
        action: Type of action (e.g., "task_completed", "task_fulfilled")
        value_change: Integer change to reputation (positive or negative)
        reason: Optional description of why reputation changed
    """
    # Get agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return False

    # Update reputation score
    agent.reputation_score += value_change
    agent.updated_at = datetime.utcnow()

    # Create reputation log entry
    log_entry = ReputationLog(
        agent_id=agent_id,
        action=action,
        value_change=value_change,
        reason=reason
    )

    db.add(log_entry)
    db.commit()

    return True


# Reputation scoring constants
REPUTATION_ACTIONS = {
    "task_completed": 10,        # +10 for completing a task
    "task_fulfilled": 5,         # +5 for posting a task that gets completed
    "positive_interaction": 2,   # +2 for positive interaction rating
    "task_failed": -5,           # -5 for task failures or timeouts
    "malicious_behavior": -10,   # -10 for reported malicious behavior
}


def apply_reputation_change(db: Session, agent_id: str, action_type: str, reason: str = ""):
    """
    Apply a standard reputation change based on action type.

    Args:
        db: Database session
        agent_id: ID of the agent
        action_type: One of the predefined action types
        reason: Optional description
    """
    if action_type not in REPUTATION_ACTIONS:
        return False

    value_change = REPUTATION_ACTIONS[action_type]
    return update_reputation(db, agent_id, action_type, value_change, reason)
