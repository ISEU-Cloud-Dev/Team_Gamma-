import asyncio
import redis.asyncio as redis
import json
from app.websocket.connection_manager import manager


async def redis_listener(redis_url: str):
    """
    Escucha Redis Pub/Sub y reenvía mensajes al connection manager.
    Se reconecta automáticamente si la conexión se cae por cualquier motivo.
    """
    while True:
        try:
            r = redis.from_url(redis_url)
            pubsub = r.pubsub()
            await pubsub.psubscribe("survey:*")
            print("[redis_listener] Suscrito a survey:* correctamente")

            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    channel = message["channel"].decode()
                    survey_id = int(channel.split(":")[1])
                    data = json.loads(message["data"])
                    await manager.broadcast(survey_id, data)

        except asyncio.CancelledError:
            # Si la app se está apagando de verdad, no reintentamos
            print("[redis_listener] Cancelado, cerrando limpiamente")
            raise

        except Exception as e:
            print(f"[redis_listener] Error: {e}. Reintentando en 2s...")
            await asyncio.sleep(2)