import redis
import json
from typing import Dict, Any, List
from ..config import settings

# Create Redis client
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
except Exception as e:
    print(f"Warning: Could not connect to Redis: {e}")
    redis_client = None


def publish_task(task_data: Dict[str, Any]) -> bool:
    """
    Publish a new task to Redis pub/sub channels.
    Broadcasts to:
    - tasks:new (general channel)
    - tasks:{capability} (for each required capability)

    Args:
        task_data: Dictionary containing task information

    Returns:
        bool: True if published successfully, False otherwise
    """
    if not redis_client:
        print("Redis not available, skipping task broadcast")
        return False

    try:
        task_json = json.dumps(task_data)

        # Publish to general tasks channel
        redis_client.publish("tasks:new", task_json)

        # Publish to capability-specific channels
        capabilities = task_data.get("required_capabilities", [])
        for cap in capabilities:
            redis_client.publish(f"tasks:{cap}", task_json)

        return True
    except Exception as e:
        print(f"Error publishing task to Redis: {e}")
        return False


def publish_notification(agent_id: str, notification_data: Dict[str, Any]) -> bool:
    """
    Publish a notification to a specific agent's channel.

    Args:
        agent_id: ID of the agent to notify
        notification_data: Dictionary containing notification information

    Returns:
        bool: True if published successfully, False otherwise
    """
    if not redis_client:
        return False

    try:
        notification_json = json.dumps(notification_data)
        redis_client.publish(f"agent:{agent_id}:notifications", notification_json)
        return True
    except Exception as e:
        print(f"Error publishing notification to Redis: {e}")
        return False


def subscribe_to_tasks(capabilities: List[str]):
    """
    Subscribe to task channels based on agent capabilities.
    Returns a pubsub object that can be used to listen for messages.

    Args:
        capabilities: List of capability strings

    Returns:
        Redis pubsub object or None if Redis is not available
    """
    if not redis_client:
        return None

    try:
        pubsub = redis_client.pubsub()
        channels = ["tasks:new"] + [f"tasks:{cap}" for cap in capabilities]
        pubsub.subscribe(channels)
        return pubsub
    except Exception as e:
        print(f"Error subscribing to task channels: {e}")
        return None


def subscribe_to_agent_notifications(agent_id: str):
    """
    Subscribe to a specific agent's notification channel.

    Args:
        agent_id: ID of the agent

    Returns:
        Redis pubsub object or None if Redis is not available
    """
    if not redis_client:
        return None

    try:
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"agent:{agent_id}:notifications")
        return pubsub
    except Exception as e:
        print(f"Error subscribing to agent notifications: {e}")
        return None
