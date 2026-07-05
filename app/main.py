from fastapi import FastAPI

app = FastAPI(
    title="Real-Time Polls API",
    description="API para crear y responder encuestas en tiempo real.",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Endpoint de verificación: confirma que la API está corriendo."""
    return {
        "status": "ok",
        "message": "Bienvenido a Real-Time Polls API"
    }