"""Generic ORM CRUD shared by the four collection routers.

`skills`, `projects`, `education` and `experience` all follow the same
five-route shape, so the querying, ordering and 404 behaviour lives here
instead of being copy-pasted four times.
"""

from typing import Any, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Base

ModelT = TypeVar("ModelT", bound=Base)

# Human-readable names for 404 messages.
LABELS: dict[str, str] = {
    "skills": "Skill",
    "projects": "Project",
    "education": "Education entry",
    "experience": "Experience entry",
}


def _label(model: type[Base]) -> str:
    return LABELS.get(model.__tablename__, model.__name__)


def list_rows(session: Session, model: type[ModelT]) -> list[ModelT]:
    """Admin controls the order; new rows still land sensibly at order 0."""
    return list(
        session.scalars(
            select(model).order_by(model.display_order.asc(), model.id.desc())
        ).all()
    )


def find_row(session: Session, model: type[ModelT], row_id: int) -> ModelT | None:
    return session.get(model, row_id)


def get_row(session: Session, model: type[ModelT], row_id: int) -> ModelT:
    row = session.get(model, row_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{_label(model)} {row_id} not found",
        )
    return row


def insert_row(
    session: Session, model: type[ModelT], values: dict[str, Any]
) -> ModelT:
    row = model(**values)
    session.add(row)
    session.commit()
    session.refresh(row)  # pick up server defaults and the new id
    return row


def update_row(
    session: Session, model: type[ModelT], row_id: int, values: dict[str, Any]
) -> ModelT:
    row = get_row(session, model, row_id)
    for key, value in values.items():
        setattr(row, key, value)
    session.commit()  # TimestampMixin.onupdate bumps updated_at
    session.refresh(row)
    return row


def delete_row(session: Session, model: type[Base], row_id: int) -> None:
    row = get_row(session, model, row_id)
    session.delete(row)
    session.commit()
