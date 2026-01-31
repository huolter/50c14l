from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Agent, Task
from ..schemas import TaskCreate, TaskComplete, TaskResponse
from ..auth import get_current_agent
from ..utils.reputation import update_reputation
from ..utils.notifications import publish_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Post a new task/request.
    """
    new_task = Task(
        requester_id=agent.id,
        title=task_data.title,
        description=task_data.description,
        required_capabilities=task_data.required_capabilities,
        payload=task_data.payload,
        priority=task_data.priority,
        expires_at=task_data.expires_at,
        status="open"
    )

    db.add(new_task)
    agent.total_tasks_posted += 1
    agent.last_active = datetime.utcnow()
    db.commit()
    db.refresh(new_task)

    # Broadcast to Redis
    publish_task({
        "id": new_task.id,
        "title": new_task.title,
        "required_capabilities": new_task.required_capabilities,
        "requester_id": new_task.requester_id,
        "created_at": new_task.created_at.isoformat()
    })

    return new_task


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    capabilities: Optional[str] = None,
    status: Optional[str] = "open",
    limit: int = 25,
    db: Session = Depends(get_db)
):
    """
    List available tasks.
    Query params:
    - capabilities: comma-separated list of capabilities
    - status: task status (open, in_progress, completed, cancelled)
    - limit: max number of results (default 25, max 100)
    """
    if limit > 100:
        limit = 100

    query = db.query(Task)

    # Filter by status
    if status:
        query = query.filter(Task.status == status)

    # Filter by capabilities (case-insensitive)
    if capabilities:
        caps_list = [c.strip().lower() for c in capabilities.split(",")]

        # Get all matching tasks and filter in Python for case-insensitive
        all_tasks = query.order_by(Task.priority.desc(), Task.created_at.desc()).all()

        # Filter tasks with case-insensitive capability matching
        matching_tasks = []
        for task in all_tasks:
            task_caps_lower = [c.lower() for c in (task.required_capabilities or [])]
            # Check if any search capability matches
            if any(search_cap in task_caps_lower for search_cap in caps_list):
                matching_tasks.append(task)

        return matching_tasks[:limit]

    # Order by priority descending, then created_at descending
    query = query.order_by(Task.priority.desc(), Task.created_at.desc())

    tasks = query.limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """
    Get task details by ID.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/claim", response_model=TaskResponse)
def claim_task(
    task_id: str,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Claim a task.
    Sets status to "in_progress" and assigns claimer_id.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "open":
        raise HTTPException(status_code=400, detail="Task is not available")

    if task.requester_id == agent.id:
        raise HTTPException(status_code=400, detail="Cannot claim your own task")

    task.claimer_id = agent.id
    task.status = "in_progress"
    task.updated_at = datetime.utcnow()
    agent.last_active = datetime.utcnow()

    db.commit()
    db.refresh(task)

    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    completion: TaskComplete,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Mark task as complete.
    Updates reputation scores for both requester and claimer.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.claimer_id != agent.id:
        raise HTTPException(status_code=403, detail="Only the claimer can complete this task")

    if task.status != "in_progress":
        raise HTTPException(status_code=400, detail="Task is not in progress")

    # Update task
    task.status = "completed"
    task.result = completion.result
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()

    # Update agent stats
    agent.total_tasks_completed += 1
    agent.last_active = datetime.utcnow()

    # Update reputation for claimer (completer)
    update_reputation(db, agent.id, "task_completed", 10, f"Completed task: {task.title}")

    # Update reputation for requester
    requester = db.query(Agent).filter(Agent.id == task.requester_id).first()
    if requester:
        update_reputation(db, requester.id, "task_fulfilled", 5, f"Task fulfilled: {task.title}")

    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}")
def cancel_task(
    task_id: str,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Cancel a task (only by creator).
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.requester_id != agent.id:
        raise HTTPException(status_code=403, detail="Only the task creator can cancel it")

    if task.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed task")

    task.status = "cancelled"
    task.updated_at = datetime.utcnow()
    agent.last_active = datetime.utcnow()

    db.commit()

    return {"message": "Task cancelled successfully"}
