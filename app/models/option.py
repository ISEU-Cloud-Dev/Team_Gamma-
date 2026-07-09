import uuid

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Option(Base):
    """
    Opción de respuesta para preguntas de tipo choice.

    Relaciones:
      - Muchas a 1 con Question
      - Muchas a Muchas con Response (a través de response_options)
    """
    __tablename__ = "options"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped["Question"] = relationship(back_populates="options")

    # Se llena en response.py vía back_populates para no duplicar la relación
    responses: Mapped[list["Response"]] = relationship(
        secondary="response_options",
        back_populates="selected_options",
    )