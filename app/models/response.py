import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import DateTime, ForeignKey, Table, Column, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

# Tabla puente para la relación Muchas a Muchas entre Response y Option.
# No es un "modelo de negocio" propio, solo une las dos tablas
# (por eso seguimos teniendo 4 modelos: Survey, Question, Option, Response).
response_options = Table(
    "response_options",
    Base.metadata,
    Column("response_id", UUID(as_uuid=True), ForeignKey("responses.id", ondelete="CASCADE"), primary_key=True),
    Column("option_id", UUID(as_uuid=True), ForeignKey("options.id", ondelete="CASCADE"), primary_key=True),
)


class Response(Base):
    """
    Respuesta anónima enviada por un participante a una encuesta completa.

    Relaciones:
      - Muchas a 1 con Survey
      - Muchas a Muchas con Option (opciones seleccionadas en preguntas de choice)

    Para preguntas de texto libre, guardamos el detalle en `text_answers`
    como JSON: {"<question_id>": "texto ingresado", ...}
    Esto evita crear un 5to modelo solo para respuestas de texto.
    """
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    text_answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    survey: Mapped["Survey"] = relationship(back_populates="responses")
    selected_options: Mapped[List["Option"]] = relationship(
        secondary=response_options,
        back_populates="responses",
    )