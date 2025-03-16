import aioredis
from typing import Dict, Any, List, Optional
import json
from app.core.config import settings

class RedisCache:
    def __init__(self):
        self.redis = aioredis.from_url(settings.REDIS_URL)
    
    async def set_event(self, event_id: str, event_data: Dict[str, Any], expire: int = 3600):
        """
        Cache event data in Redis
        """
        await self.redis.set(
            f"event:{event_id}",
            json.dumps(event_data),
            ex=expire
        )
        
        # Add to recent events list
        await self.redis.zadd(
            "recent_events",
            {event_id: event_data.get('timestamp', 0)}
        )
    
    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached event data
        """
        data = await self.redis.get(f"event:{event_id}")
        if data:
            return json.loads(data)
        return None
    
    async def get_recent_events(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent events with pagination
        """
        # Get event IDs from sorted set
        event_ids = await self.redis.zrevrange(
            "recent_events",
            skip,
            skip + limit - 1
        )
        
        events = []
        for event_id in event_ids:
            event_data = await self.get_event(event_id.decode())
            if event_data:
                events.append(event_data)
        
        return events

redis_cache = RedisCache()