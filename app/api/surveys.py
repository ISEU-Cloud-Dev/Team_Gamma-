from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.survey import Survey
from app.models.question import Question
from app.models.option import Option
from app.schemas.survey import SurveyCreate, SurveyRead, SurveyListResponse

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


@router.get("", response_model=SurveyListResponse)
async def list_surveys(
    page: int = Query(1, ge=1, description="Número de página, empieza en 1"),
    size: int = Query(10, ge=1, le=100, description="Encuestas por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista las encuestas de forma paginada, con sus preguntas y opciones
    ya incluidas.

    Usamos selectinload para traer preguntas y opciones en 2 consultas
    extra (una por cada nivel de relación), en vez de 1 consulta por
    cada encuesta -- eso es lo que evita el problema N+1.
    """
    offset = (page - 1) * size

    total = (await db.execute(select(func.count()).select_from(Survey))).scalar_one()

    stmt = (
        select(Survey)
        .options(
            selectinload(Survey.questions).selectinload(Question.options)
        )
        .order_by(Survey.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    surveys = result.scalars().all()

    return SurveyListResponse(items=surveys, total=total, page=page, size=size)