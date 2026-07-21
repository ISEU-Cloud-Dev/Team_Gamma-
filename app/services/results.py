"""
Lógica de conteo de votos, separada del endpoint para que el WebSocket
(app/websocket/redis_listener.py) pueda reutilizar exactamente esta misma
función para el broadcast en tiempo real, en vez de reimplementar el
conteo por su lado.
"""
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.survey import Survey
from app.models.question import Question
from app.models.response import Response as ResponseModel, response_options


async def compute_survey_results(db: AsyncSession, survey_id: uuid.UUID) -> dict | None:
    """
    Calcula el conteo de votos por opción, agrupado por pregunta.

    Devuelve None si la encuesta no existe (el llamador decide qué hacer
    con eso -- el endpoint HTTP lo convierte en 404).
    """
    stmt = (
        select(Survey)
        .options(selectinload(Survey.questions).selectinload(Question.options))
        .where(Survey.id == survey_id)
    )
    survey = (await db.execute(stmt)).scalar_one_or_none()
    if survey is None:
        return None

    all_option_ids = [
        option.id for question in survey.questions for option in question.options
    ]

    votes_by_option: dict[uuid.UUID, int] = {}
    if all_option_ids:
        count_stmt = (
            select(response_options.c.option_id, func.count().label("votes"))
            .where(response_options.c.option_id.in_(all_option_ids))
            .group_by(response_options.c.option_id)
        )
        for option_id, votes in await db.execute(count_stmt):
            votes_by_option[option_id] = votes

    total_responses = (
        await db.execute(
            select(func.count())
            .select_from(ResponseModel)
            .where(ResponseModel.survey_id == survey_id)
        )
    ).scalar_one()

    questions_out = [
        {
            "question_id": question.id,
            "text": question.text,
            "options": [
                {
                    "option_id": option.id,
                    "text": option.text,
                    "votes": votes_by_option.get(option.id, 0),
                }
                for option in question.options
            ],
        }
        for question in survey.questions
    ]

    return {
        "survey_id": survey_id,
        "total_responses": total_responses,
        "questions": questions_out,
    }