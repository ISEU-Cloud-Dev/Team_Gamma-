"""
Configuración central de la base de datos.

Usamos SQLAlchemy 2.0 en modo async porque FastAPI es async-first,
y así evitamos bloquear el event loop en cada query.
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Tu docker-compose.yml ya define DATABASE_URL como:
#   postgresql://postgres:postgres@db:5432/polls_db
# SQLAlchemy async necesita el driver "asyncpg" explícito en la URL,
# así que lo agregamos automáticamente si no viene incluido, para no
# tener que tocar el docker-compose.yml ni pedir una variable nueva.
_raw_url = os.getenv("DATABASE_URL")
if not _raw_url:
    raise RuntimeError(
        "Falta la variable de entorno DATABASE_URL. Si corres con "
        "docker-compose, ya viene definida en el servicio 'web'. Si corres "
        "en local (fuera de Docker), expórtala apuntando a localhost, ej.:\n"
        "  export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/polls_db"
    )

if _raw_url.startswith("postgresql://"):
    DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = _raw_url

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # evita errores al acceder a atributos tras el commit
)


class Base(DeclarativeBase):
    """Clase base declarativa de la que heredan todos los modelos."""
    pass


async def get_db():
    """Dependency de FastAPI para inyectar una sesión de DB por request."""
    async with AsyncSessionLocal() as session:
        yield session