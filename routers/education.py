"""Education CRUD. Public reads, admin-only writes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from auth import AdminRequired
from database import get_db, next_display_order
from models import Education
from routers import crud
from schemas import EducationIn, EducationOut

router = APIRouter(prefix="/api/education", tags=["education"])

Db = Annotated[Session, Depends(get_db)]


def to_values(payload: EducationIn, session: Session) -> dict[str, Any]:
    return {
        "institution": payload.institution,
        "degree": payload.degree,
        "field": payload.field,
        "location": payload.location,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "grade": payload.grade,
        "description": payload.description,
        "display_order": (
            payload.display_order
            if payload.display_order is not None
            else next_display_order(session, Education)
        ),
    }


@router.get("", response_model=list[EducationOut])
def list_education(session: Db) -> list[Education]:
    return crud.list_rows(session, Education)


@router.get("/{entry_id}", response_model=EducationOut)
def get_education(entry_id: int, session: Db) -> Education:
    return crud.get_row(session, Education, entry_id)


@router.post(
    "",
    response_model=EducationOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[AdminRequired],
)
def create_education(payload: EducationIn, session: Db) -> Education:
    return crud.insert_row(session, Education, to_values(payload, session))


@router.put(
    "/{entry_id}", response_model=EducationOut, dependencies=[AdminRequired]
)
def update_education(
    entry_id: int, payload: EducationIn, session: Db
) -> Education:
    values = to_values(payload, session)
    if payload.display_order is None:
        values["display_order"] = crud.get_row(
            session, Education, entry_id
        ).display_order
    return crud.update_row(session, Education, entry_id, values)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminRequired],
)
def delete_education(entry_id: int, session: Db) -> Response:
    crud.delete_row(session, Education, entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
