"""
Importa todos los modelos aquí para que:
1. Alembic (autogenerate) pueda detectarlos al escanear Base.metadata.
2. Las relaciones entre modelos (que se resuelven por nombre de clase,
   ej. "Question") encuentren la clase real sin importarla manualmente
   en cada archivo.
"""
from app.models.survey import Survey
from app.models.question import Question, QuestionType
from app.models.option import Option
from app.models.response import Response, response_options

__all__ = [
    "Survey",
    "Question",
    "QuestionType",
    "Option",
    "Response",
    "response_options",
]