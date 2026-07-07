import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QuestionAnswer(BaseModel):
    """
    Una respuesta a UNA pregunta dentro del envío completo.
    - Para preguntas de choice: se llenan option_ids.
    - Para preguntas de texto libre: se llena text.
    """
    question_id: uuid.UUID
    option_ids: List[uuid.UUID] = []
    text: Optional[str] = Field(default=None, max_length=2000)


class ResponseCreate(BaseModel):
    answers: List[QuestionAnswer] = Field(min_length=1)


class ResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    survey_id: uuid.UUID
    created_at: datetime
    text_answers: Optional[Dict[str, str]] = None
    # No exponemos selected_options como objetos completos aquí para
    # mantener la respuesta liviana; si se necesita el detalle completo
    # se puede hacer GET /surveys/{id}/resultados (fuera de este ticket).