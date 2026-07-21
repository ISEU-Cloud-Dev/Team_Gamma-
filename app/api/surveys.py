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
from app.schemas.results import SurveyResults
from app.services.results import compute_survey_results

router = APIRouter(prefix="/api/v1/surveys", tags=["surveys"])


@router.post("", response_model=SurveyRead, status_code=status.HTTP_201_CREATED)
async def create_survey(payload: SurveyCreate, db: AsyncSession = Depends(get_db)):
    survey = Survey(title=payload.title, description=payload.description)
    for question_data in payload.questions:
        question = Question(
            text=question_data.text, type=question_data.type, order=question_data.order
        )
        for option_data in question_data.options:
            question.options.append(Option(text=option_data.text, order=option_data.order))
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
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * size
    total = (await db.execute(select(func.count()).select_from(Survey))).scalar_one()
    stmt = (
        select(Survey)
        .options(selectinload(Survey.questions).selectinload(Question.options))
        .order_by(Survey.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    surveys = (await db.execute(stmt)).scalars().all()
    return SurveyListResponse(items=surveys, total=total, page=page, size=size)


@router.get("/{survey_id}", response_model=SurveyRead)
async def get_survey(survey_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Devuelve el detalle completo de UNA encuesta, con sus preguntas y
    opciones anidadas -- el frontend necesita los IDs de cada pregunta
    y opción para poder enviar respuestas después.
    """
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
    return survey


@router.get("/{survey_id}/results", response_model=SurveyResults)
async def get_survey_results(survey_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Devuelve el conteo de votos por opción, agrupado por pregunta.

    La lógica real vive en app/services/results.py para que el WebSocket
    pueda reutilizarla en el broadcast, sin duplicar la consulta.
    """
    results = await compute_survey_results(db, survey_id)
    if results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe una encuesta con id {survey_id}",
        )
    return results


@router.post(
    "/{survey_id}/responses", response_model=ResponseRead, status_code=status.HTTP_201_CREATED
)
async def submit_response(
    survey_id: uuid.UUID, payload: ResponseCreate, db: AsyncSession = Depends(get_db)
):
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

    questions_by_id = {q.id: q for q in survey.questions}
    text_answers: dict[str, str] = {}
    selected_options: list[Option] = []

    for answer in payload.answers:
        question = questions_by_id.get(answer.question_id)
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La pregunta {answer.question_id} no pertenece a la encuesta {survey_id}",
            )
        valid_option_ids = {o.id for o in question.options}
        for option_id in answer.option_ids:
            if option_id not in valid_option_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La opción {option_id} no pertenece a la pregunta {answer.question_id}",
                )
        selected_options.extend(o for o in question.options if o.id in answer.option_ids)
        if answer.text is not None:
            text_answers[str(answer.question_id)] = answer.text

    response = ResponseModel(
        survey_id=survey.id, text_answers=text_answers or None, selected_options=selected_options
    )
    db.add(response)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(response)
    return response