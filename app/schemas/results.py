import uuid
from typing import List

from pydantic import BaseModel


class OptionResult(BaseModel):
    option_id: uuid.UUID
    text: str
    votes: int


class QuestionResult(BaseModel):
    question_id: uuid.UUID
    text: str
    options: List[OptionResult]


class SurveyResults(BaseModel):
    survey_id: uuid.UUID
    total_responses: int
    questions: List[QuestionResult]