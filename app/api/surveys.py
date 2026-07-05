from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.survey import Survey
from app.models.question import Question
from app.models.option import Option
from app.schemas.survey import SurveyCreate, SurveyRead

router = APIRouter(prefix="/api/v1/surveys", tags=["surveys"])


@router.post("", response_model=SurveyRead, status_code=status.HTTP_201_CREATED)
async def create_survey(payload: SurveyCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea una encuesta junto con sus preguntas y opciones en una sola
    transacción: si algo falla a mitad de camino (ej. una FK inválida),
    no se guarda nada -- todo o nada.
    """
    survey = Survey(
        title=payload.title,
        description=payload.description,
    )

    for question_data in payload.questions:
        question = Question(
            text=question_data.text,
            type=question_data.type,
            order=question_data.order,
        )
        for option_data in question_data.options:
            option = Option(
                text=option_data.text,
                order=option_data.order,
            )
            question.options.append(option)
        survey.questions.append(question)

    db.add(survey)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(survey, attribute_names=["questions"])
    for question in survey.questions:
        await db.refresh(question, attribute_names=["options"])

    return survey