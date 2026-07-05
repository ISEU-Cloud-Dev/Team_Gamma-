"""
Schemas de Pydantic para Survey/Question/Option.

Separamos "Create" (lo que manda el cliente) de "Read" (lo que devolvemos),
porque el cliente no debe poder mandar un "id" o "created_at" al crear algo.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.question import QuestionType


# ---------- OPTION ----------

class OptionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=255)
    order: int = 0


class OptionRead(BaseModel):
    # from_attributes=True permite construir este schema directo desde
    # el objeto ORM (Option), sin convertirlo a dict a mano.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    order: int


# ---------- QUESTION ----------

class QuestionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    type: QuestionType = QuestionType.SINGLE_CHOICE
    order: int = 0
    # Si type == TEXT, se puede mandar options vacío o omitirlo.
    options: List[OptionCreate] = []


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    type: QuestionType
    order: int
    options: List[OptionRead] = []


# ---------- SURVEY ----------

class SurveyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    questions: List[QuestionCreate] = []


class SurveyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    created_at: datetime
    questions: List[QuestionRead] = []


class SurveyListResponse(BaseModel):
    """Wrapper para paginación simple basada en page/size."""
    items: List[SurveyRead]
    total: int
    page: int
    size: int