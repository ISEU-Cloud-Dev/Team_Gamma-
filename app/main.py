import asyncio
import os
from fastapi import FastAPI
from app.api.surveys import router as surveys_router
from app.websocket.routes import router as websocket_router
from app.websocket.redis_listener import redis_listener

app = FastAPI(
    title="Real-Time Polls API",
    description="API REST para crear, listar y responder encuestas en tiempo real.",
    version="1.0.0",
)

# Rutas de encuestas
app.include_router(surveys_router)

# Rutas de WebSocket
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Endpoint de verificación: confirma que la API está corriendo."""
    return {
        "status": "ok",
        "message": "Bienvenido a Real-Time Polls API"
    }


@app.get("/health")
async def health_check():
    """Endpoint simple para confirmar que el servidor está vivo."""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    asyncio.create_task(redis_listener(redis_url))