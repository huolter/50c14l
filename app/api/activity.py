from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
from datetime import datetime
from ..database import get_db
from ..models import Agent, Task, Interaction, ReputationLog

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/recent")
def get_recent_activity(limit: int = 100, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get recent activity across the platform.
    Returns aggregated events from agents, tasks, interactions, and reputation changes.
    """
    events = []

    # Get recent agent registrations
    recent_agents = db.query(Agent).order_by(desc(Agent.created_at)).limit(50).all()
    for agent in recent_agents:
        events.append({
            "type": "agent_registered",
            "timestamp": agent.created_at.isoformat(),
            "summary": f"🤖 Agent '{agent.name}' registered",
            "details": {
                "agent_id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities,
                "reputation_score": agent.reputation_score
            }
        })

    # Get recent tasks
    recent_tasks = db.query(Task).order_by(desc(Task.created_at)).limit(50).all()
    for task in recent_tasks:
        requester = db.query(Agent).filter(Agent.id == task.requester_id).first()
        requester_name = requester.name if requester else "Unknown"

        if task.status == "open":
            events.append({
                "type": "task_created",
                "timestamp": task.created_at.isoformat(),
                "summary": f"📋 Task '{task.title}' posted by {requester_name}",
                "details": {
                    "task_id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "requester": requester_name,
                    "required_capabilities": task.required_capabilities,
                    "status": task.status,
                    "priority": task.priority
                }
            })
        elif task.status == "in_progress" and task.claimer_id:
            claimer = db.query(Agent).filter(Agent.id == task.claimer_id).first()
            claimer_name = claimer.name if claimer else "Unknown"
            events.append({
                "type": "task_claimed",
                "timestamp": task.updated_at.isoformat(),
                "summary": f"✋ Task '{task.title}' claimed by {claimer_name}",
                "details": {
                    "task_id": task.id,
                    "title": task.title,
                    "claimer": claimer_name,
                    "requester": requester_name,
                    "status": task.status
                }
            })
        elif task.status == "completed" and task.completed_at:
            claimer = db.query(Agent).filter(Agent.id == task.claimer_id).first() if task.claimer_id else None
            claimer_name = claimer.name if claimer else "Unknown"
            events.append({
                "type": "task_completed",
                "timestamp": task.completed_at.isoformat(),
                "summary": f"✅ Task '{task.title}' completed by {claimer_name}",
                "details": {
                    "task_id": task.id,
                    "title": task.title,
                    "claimer": claimer_name,
                    "requester": requester_name,
                    "completed_at": task.completed_at.isoformat(),
                    "result": task.result
                }
            })

    # Get recent interactions
    recent_interactions = db.query(Interaction).order_by(desc(Interaction.created_at)).limit(50).all()
    for interaction in recent_interactions:
        sender = db.query(Agent).filter(Agent.id == interaction.sender_id).first()
        recipient = db.query(Agent).filter(Agent.id == interaction.recipient_id).first()
        sender_name = sender.name if sender else "Unknown"
        recipient_name = recipient.name if recipient else "Unknown"

        events.append({
            "type": "interaction",
            "timestamp": interaction.created_at.isoformat(),
            "summary": f"💬 {sender_name} → {recipient_name}: {interaction.message_type}",
            "details": {
                "interaction_id": interaction.id,
                "sender": sender_name,
                "recipient": recipient_name,
                "message_type": interaction.message_type,
                "status": interaction.status,
                "payload": interaction.payload
            }
        })

    # Get recent reputation changes
    recent_reputation = db.query(ReputationLog).order_by(desc(ReputationLog.created_at)).limit(50).all()
    for rep_log in recent_reputation:
        agent = db.query(Agent).filter(Agent.id == rep_log.agent_id).first()
        agent_name = agent.name if agent else "Unknown"

        change_icon = "📈" if rep_log.value_change > 0 else "📉"
        events.append({
            "type": "reputation_change",
            "timestamp": rep_log.created_at.isoformat(),
            "summary": f"{change_icon} {agent_name}: {rep_log.value_change:+d} reputation ({rep_log.action})",
            "details": {
                "agent": agent_name,
                "action": rep_log.action,
                "value_change": rep_log.value_change,
                "reason": rep_log.reason,
                "new_score": agent.reputation_score if agent else None
            }
        })

    # Sort all events by timestamp (newest first)
    events.sort(key=lambda x: x["timestamp"], reverse=True)

    # Return limited number of events
    return events[:limit]
