"""Work experience CRUD. Public reads, admin-only writes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from auth import AdminRequired
from database import get_db, next_display_order
from models import Experience, join_csv
from routers import crud
from schemas import ExperienceIn, ExperienceOut

router = APIRouter(prefix="/api/experience", tags=["experience"])

Db = Annotated[Session, Depends(get_db)]


def to_values(payload: ExperienceIn, session: Session) -> dict[str, Any]:
    return {
        "company": payload.company,
        "role": payload.role,
        "location": payload.location,
        "employment_type": payload.employment_type,
        "start_date": payload.start_date,
        # A current role has no end date, whatever the form sent.
        "end_date": "" if payload.is_current else payload.end_date,
        "is_current": int(payload.is_current),
        "description": payload.description,
        "tech_stack": join_csv(payload.tech_stack),
        "display_order": (
            payload.display_order
            if payload.display_order is not None
            else next_display_order(session, Experience)
        ),
    }


@router.get("", response_model=list[ExperienceOut])
def list_experience(session: Db) -> list[Experience]:
    return crud.list_rows(session, Experience)


@router.get("/{entry_id}", response_model=ExperienceOut)
def get_experience(entry_id: int, session: Db) -> Experience:
    return crud.get_row(session, Experience, entry_id)


@router.post(
    "",
    response_model=ExperienceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[AdminRequired],
)
def create_experience(payload: ExperienceIn, session: Db) -> Experience:
    return crud.insert_row(session, Experience, to_values(payload, session))


@router.put(
    "/{entry_id}", response_model=ExperienceOut, dependencies=[AdminRequired]
)
def update_experience(
    entry_id: int, payload: ExperienceIn, session: Db
) -> Experience:
    values = to_values(payload, session)
    if payload.display_order is None:
        values["display_order"] = crud.get_row(
            session, Experience, entry_id
        ).display_order
    return crud.update_row(session, Experience, entry_id, values)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminRequired],
)
def delete_experience(entry_id: int, session: Db) -> Response:
    crud.delete_row(session, Experience, entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
