import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import String, DateTime
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Survey(Base):
    """
    Encuesta. Es la raíz del árbol: contiene preguntas y recibe respuestas.

    Relaciones:
      - 1 a Muchos con Question
      - 1 a Muchos con Response
    """
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # cascade="all, delete-orphan": si se borra la encuesta, se borran
    # sus preguntas y respuestas asociadas (borrado en cascada).
    questions: Mapped[List["Question"]] = relationship(
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="Question.order",
    )
    responses: Mapped[List["Response"]] = relationship(
        back_populates="survey",
        cascade="all, delete-orphan",
    )