import json
from typing import Any, Optional
from app.core.clients import redis_client

def get_json(key: str) -> Optional[Any]:
    """Get a JSON object from Redis by key."""
    val = redis_client.get(key)
    if val is None:
        return None
    try:
        return json.loads(val)
    except Exception:
        return None

def set_json(key: str, value: Any, ttl_seconds: int) -> None:
    """Set a JSON-serializable value with TTL."""
    redis_client.set(key, json.dumps(value), ex=ttl_seconds)
