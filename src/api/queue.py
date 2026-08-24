import redis
import json
import os
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class TaskQueue:
    """Redis-based task queue."""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = None

    async def connect(self):
        """Connect to Redis."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.redis_client.ping()
        logger.info(f"Redis queue connected to {self.redis_url}")

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis queue disconnected")

    async def enqueue(self, task_id: str, task_type: str, payload: Dict[str, Any], priority: str = "normal"):
        """Enqueue a task."""
        queue_name = f"queue:{task_type}:{priority}"
        task_data = {
            "task_id": task_id,
            "type": task_type,
            "payload": json.dumps(payload),
        }
        self.redis_client.rpush(queue_name, json.dumps(task_data))
        logger.info(f"Task {task_id} enqueued to {queue_name}")

    async def dequeue(self, task_type: str, timeout: int = 0):
        """Dequeue a task, blocking until one is available or timeout expires."""
        queue_names = [
            f"queue:{task_type}:high",
            f"queue:{task_type}:normal",
            f"queue:{task_type}:low",
        ]
        result = self.redis_client.blpop(queue_names, timeout=timeout)
        if result:
            _, task_json = result
            return json.loads(task_json)
        return None

    async def get_queue_size(self, task_type: str) -> int:
        """Get total pending tasks across all priorities."""
        high = self.redis_client.llen(f"queue:{task_type}:high")
        normal = self.redis_client.llen(f"queue:{task_type}:normal")
        low = self.redis_client.llen(f"queue:{task_type}:low")
        return high + normal + low

    async def set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Cache a value with TTL."""
        self.redis_client.setex(key, ttl, json.dumps(value))

    async def get_cache(self, key: str) -> Any:
        """Get a cached value."""
        value = self.redis_client.get(key)
        return json.loads(value) if value else None
