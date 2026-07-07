import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.survey import Survey
from app.models.question import Question
from app.models.option import Option
from app.models.response import Response as ResponseModel
from app.schemas.survey import SurveyCreate, SurveyRead, SurveyListResponse
from app.schemas.response import ResponseCreate, ResponseRead

router = APIRouter(prefix="/api/v1/surveys", tags=["surveys"])


@router.post("", response_model=SurveyRead, status_code=status.HTTP_201_CREATED)
async def create_survey(payload: SurveyCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea una encuesta junto con sus preguntas y opciones en una sola
    transacción: si algo falla a mitad de camino (ej. una FK inválida),
    no se guarda nada -- todo o nada.
    """
    # Construimos el árbol completo de objetos ORM en memoria ANTES de
    # tocar la base de datos. SQLAlchemy se encarga de asignarles los IDs
    # de padre (survey_id, question_id) automáticamente al hacer flush,
    # gracias a las relaciones definidas con back_populates.
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

    # session.add + commit: como estamos dentro de una única sesión y
    # no hacemos commits parciales, si algo lanza una excepción antes del
    # commit, la sesión se descarta sin haber persistido nada.
    db.add(survey)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    # Refrescamos con las relaciones cargadas para que la respuesta
    # incluya preguntas y opciones con sus IDs ya generados.
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


@router.post(
    "/{survey_id}/responses",
    response_model=ResponseRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_response(
    survey_id: uuid.UUID,
    payload: ResponseCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra una respuesta completa a una encuesta.

    Validaciones:
      1. La encuesta debe existir (404 si no).
      2. Cada pregunta respondida debe pertenecer a esa encuesta (400 si no).
      3. Cada opción elegida debe pertenecer a esa pregunta (400 si no).
    """
    # Cargamos la encuesta con sus preguntas Y opciones ya incluidas,
    # para poder validar todo sin hacer una consulta extra por cada pregunta.
    stmt = (
        select(Survey)
        .options(selectinload(Survey.questions).selectinload(Question.options))
        .where(Survey.id == survey_id)
    )
    survey = (await db.execute(stmt)).scalar_one_or_none()
    if survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe una encuesta con id {survey_id}",
        )

    questions_by_id = {question.id: question for question in survey.questions}
    text_answers: dict[str, str] = {}
    selected_options: list[Option] = []

    for answer in payload.answers:
        question = questions_by_id.get(answer.question_id)
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"La pregunta {answer.question_id} no pertenece "
                    f"a la encuesta {survey_id}"
                ),
            )

        valid_option_ids = {option.id for option in question.options}
        for option_id in answer.option_ids:
            if option_id not in valid_option_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"La opción {option_id} no pertenece "
                        f"a la pregunta {answer.question_id}"
                    ),
                )

        selected_options.extend(
            option for option in question.options if option.id in answer.option_ids
        )

        if answer.text is not None:
            text_answers[str(answer.question_id)] = answer.text

    response = ResponseModel(
        survey_id=survey.id,
        text_answers=text_answers or None,
        selected_options=selected_options,
    )
    db.add(response)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(response)
    return response