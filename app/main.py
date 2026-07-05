import asyncio
import os
from fastapi import FastAPI
from app.websocket.routes import router as websocket_router
from app.websocket.redis_listener import redis_listener

app = FastAPI(
    title="Real-Time Polls API",
    description="API para crear y responder encuestas en tiempo real.",
    version="1.0.0"
)

app.include_router(websocket_router)

@app.get("/")
async def root():
    """Endpoint de verificación: confirma que la API está corriendo."""
    return {
        "status": "ok",
        "message": "Bienvenido a Real-Time Polls API"
    }

@app.on_event("startup")
async def startup_event():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    asyncio.create_task(redis_listener(redis_url))