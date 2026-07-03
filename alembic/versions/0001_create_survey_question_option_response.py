"""create survey, question, option, response tables

Revision ID: 0001
Revises:
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # create_type=True (default) hace que SQLAlchemy cree el ENUM
    # automáticamente la primera vez que se usa en create_table.
    # No lo creamos a mano para evitar el "CREATE TYPE" duplicado.
    question_type_enum = postgresql.ENUM(
        "single_choice", "multiple_choice", "text",
        name="question_type",
    )

    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "survey_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("type", question_type_enum, nullable=False, server_default="single_choice"),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_questions_survey_id", "questions", ["survey_id"])

    op.create_table(
        "options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "question_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("text", sa.String(255), nullable=False),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_options_question_id", "options", ["question_id"])

    op.create_table(
        "responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "survey_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("text_answers", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_responses_survey_id", "responses", ["survey_id"])

    op.create_table(
        "response_options",
        sa.Column(
            "response_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("responses.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column(
            "option_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("options.id", ondelete="CASCADE"), primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("response_options")
    op.drop_table("responses")
    op.drop_table("options")
    op.drop_table("questions")
    op.drop_table("surveys")
    postgresql.ENUM(name="question_type").drop(op.get_bind(), checkfirst=True)