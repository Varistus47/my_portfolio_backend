"""One aggregate endpoint so the home page makes a single request."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Education, Experience, Project, Skill
from routers import crud
from routers.profile import fetch_profile_row
from schemas import PortfolioOut

router = APIRouter(prefix="/api", tags=["portfolio"])

Db = Annotated[Session, Depends(get_db)]


@router.get("/portfolio", response_model=PortfolioOut)
def get_portfolio(session: Db) -> PortfolioOut:
    return PortfolioOut.model_validate(
        {
            "profile": fetch_profile_row(session),
            "skills": crud.list_rows(session, Skill),
            "projects": crud.list_rows(session, Project),
            "education": crud.list_rows(session, Education),
            "experience": crud.list_rows(session, Experience),
        }
    )
