"""Skills CRUD. Public reads, admin-only writes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from auth import AdminRequired
from database import get_db, next_display_order
from models import Skill
from routers import crud
from schemas import SkillIn, SkillOut

router = APIRouter(prefix="/api/skills", tags=["skills"])

Db = Annotated[Session, Depends(get_db)]


def to_values(payload: SkillIn, session: Session) -> dict[str, Any]:
    return {
        "name": payload.name,
        "category": payload.category or "Other",
        "level": payload.level,
        "display_order": (
            payload.display_order
            if payload.display_order is not None
            else next_display_order(session, Skill)
        ),
    }


@router.get("", response_model=list[SkillOut])
def list_skills(
    session: Db,
    category: Annotated[str | None, Query(max_length=80)] = None,
) -> list[Skill]:
    rows = crud.list_rows(session, Skill)
    if category:
        rows = [row for row in rows if row.category == category]
    return rows


@router.get("/{skill_id}", response_model=SkillOut)
def get_skill(skill_id: int, session: Db) -> Skill:
    return crud.get_row(session, Skill, skill_id)


@router.post(
    "",
    response_model=SkillOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[AdminRequired],
)
def create_skill(payload: SkillIn, session: Db) -> Skill:
    return crud.insert_row(session, Skill, to_values(payload, session))


@router.put("/{skill_id}", response_model=SkillOut, dependencies=[AdminRequired])
def update_skill(skill_id: int, payload: SkillIn, session: Db) -> Skill:
    values = to_values(payload, session)
    if payload.display_order is None:
        # Keep the existing position when the form omits it.
        values["display_order"] = crud.get_row(session, Skill, skill_id).display_order
    return crud.update_row(session, Skill, skill_id, values)


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminRequired],
)
def delete_skill(skill_id: int, session: Db) -> Response:
    crud.delete_row(session, Skill, skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
