import uuid
from typing import List

from sqlalchemy import String, ForeignKey, Integer, Enum
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.database import Base


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"      # radio button, una sola opción
    MULTIPLE_CHOICE = "multiple_choice"  # checkboxes, varias opciones
    TEXT = "text"                        # respuesta libre, sin opciones


class Question(Base):
    """
    Pregunta dentro de una encuesta.

    Relaciones:
      - Muchas a 1 con Survey
      - 1 a Muchos con Option
    """
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    survey_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[QuestionType] = mapped_column(
        Enum(
            QuestionType,
            name="question_type",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=QuestionType.SINGLE_CHOICE,
    )
    order: Mapped[int] = mapped_column(Integer, default=0)  # orden de aparición

    survey: Mapped["Survey"] = relationship(back_populates="questions")
    options: Mapped[List["Option"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Option.order",
    )