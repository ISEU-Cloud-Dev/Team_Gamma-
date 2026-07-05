import redis.asyncio as redis
import json
from app.websocket.connection_manager import manager

async def redis_listener(redis_url: str):
    r = redis.from_url(redis_url)
    pubsub = r.pubsub()
    await pubsub.psubscribe("survey:*")

    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            channel = message["channel"].decode()
            survey_id = int(channel.split(":")[1])
            data = json.loads(message["data"])
            await manager.broadcast(survey_id, data)