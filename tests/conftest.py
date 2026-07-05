"""
Fixtures compartidos para todas las pruebas.

Usamos SQLite en memoria en vez de Postgres real para que las pruebas
corran rápido y sin depender de que Docker esté levantado. Esto es
posible porque los modelos usan el tipo `Uuid` genérico de SQLAlchemy
(no el UUID específico de Postgres).
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from fastapi import FastAPI
from app.db.database import Base, get_db
from app.api.surveys import router as surveys_router


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app = FastAPI()
    app.include_router(surveys_router)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await engine.dispose()


@pytest.fixture
def survey_payload():
    """Payload reutilizable para crear una encuesta de prueba."""
    return {
        "title": "Encuesta de prueba",
        "description": "Para pruebas automatizadas",
        "questions": [
            {
                "text": "¿Cuál es tu color favorito?",
                "type": "single_choice",
                "order": 0,
                "options": [
                    {"text": "Rojo", "order": 0},
                    {"text": "Azul", "order": 1},
                ],
            },
            {
                "text": "Comentarios",
                "type": "text",
                "order": 1,
                "options": [],
            },
        ],
    }