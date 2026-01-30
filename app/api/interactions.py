from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Agent, Interaction
from ..schemas import InteractionMessage, InteractionResponse
from ..auth import get_current_agent
import httpx

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/message", response_model=InteractionResponse)
async def send_message(
    message: InteractionMessage,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Send a direct message to another agent.
    Calls recipient's webhook if configured.
    """
    # Check if recipient exists
    recipient = db.query(Agent).filter(Agent.id == message.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient agent not found")

    if not recipient.is_active:
        raise HTTPException(status_code=400, detail="Recipient agent is not active")

    # Create interaction record
    interaction = Interaction(
        sender_id=agent.id,
        recipient_id=message.recipient_id,
        message_type=message.message_type,
        payload=message.payload,
        status="sent"
    )

    db.add(interaction)
    agent.last_active = datetime.utcnow()
    db.commit()
    db.refresh(interaction)

    # Try to call recipient's webhook if they have one
    webhook_url = recipient.endpoints.get("webhook") if isinstance(recipient.endpoints, dict) else None

    if webhook_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json={
                        "sender_id": agent.id,
                        "sender_name": agent.name,
                        "message_type": message.message_type,
                        "payload": message.payload,
                        "interaction_id": interaction.id
                    }
                )
                if response.status_code == 200:
                    interaction.status = "delivered"
                else:
                    interaction.status = "failed"
        except Exception as e:
            interaction.status = "failed"
            print(f"Webhook delivery failed: {e}")

        db.commit()
        db.refresh(interaction)

    return interaction


@router.get("/history", response_model=List[InteractionResponse])
def get_interaction_history(
    with_agent_id: Optional[str] = None,
    limit: int = 50,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Get interaction history for the authenticated agent.
    Optionally filter by a specific agent.
    """
    if limit > 100:
        limit = 100

    query = db.query(Interaction).filter(
        (Interaction.sender_id == agent.id) | (Interaction.recipient_id == agent.id)
    )

    # Filter by specific agent if provided
    if with_agent_id:
        query = query.filter(
            ((Interaction.sender_id == agent.id) & (Interaction.recipient_id == with_agent_id)) |
            ((Interaction.sender_id == with_agent_id) & (Interaction.recipient_id == agent.id))
        )

    # Order by most recent first
    interactions = query.order_by(Interaction.created_at.desc()).limit(limit).all()

    agent.last_active = datetime.utcnow()
    db.commit()

    return interactions


@router.post("/callback")
async def receive_callback(payload: dict):
    """
    Webhook endpoint for agents to receive messages.
    This is a generic endpoint - agents should register their own webhook URLs.
    """
    # This is a placeholder - agents will typically host their own webhooks
    return {
        "status": "received",
        "message": "Callback received successfully"
    }
