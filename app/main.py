from fastapi import FastAPI

from app.api.surveys import router as surveys_router

app = FastAPI(
    title="Real-Time Polls API",
    description="API REST para crear, listar y responder encuestas en tiempo real.",
    version="0.1.0",
)

app.include_router(surveys_router)


@app.get("/health")
async def health_check():
    """Endpoint simple para confirmar que el servidor está vivo."""
    return {"status": "ok"}