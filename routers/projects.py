"""Projects CRUD plus per-project image upload.

Deleting a project (or replacing its image) also unlinks the file on disk, so
the uploads directory does not accumulate orphans.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from auth import AdminRequired
from database import get_db, next_display_order
from models import Project, join_csv
from routers import crud
from schemas import ImageOut, ProjectIn, ProjectOut
from storage import delete_upload, public_url, save_image

router = APIRouter(prefix="/api/projects", tags=["projects"])

Db = Annotated[Session, Depends(get_db)]


def to_values(payload: ProjectIn, session: Session) -> dict[str, Any]:
    return {
        "title": payload.title,
        "short_description": payload.short_description,
        "description": payload.description,
        "tech_stack": join_csv(payload.tech_stack),
        "github_url": payload.github_url,
        "live_url": payload.live_url,
        "featured": int(payload.featured),
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "display_order": (
            payload.display_order
            if payload.display_order is not None
            else next_display_order(session, Project)
        ),
    }


@router.get("", response_model=list[ProjectOut])
def list_projects(
    session: Db,
    featured: Annotated[bool | None, Query()] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
) -> list[Project]:
    rows = crud.list_rows(session, Project)
    if featured is not None:
        rows = [row for row in rows if bool(row.featured) is featured]
    if limit is not None:
        rows = rows[:limit]
    return rows


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, session: Db) -> Project:
    return crud.get_row(session, Project, project_id)


@router.post(
    "",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[AdminRequired],
)
def create_project(payload: ProjectIn, session: Db) -> Project:
    return crud.insert_row(session, Project, to_values(payload, session))


@router.put(
    "/{project_id}", response_model=ProjectOut, dependencies=[AdminRequired]
)
def update_project(project_id: int, payload: ProjectIn, session: Db) -> Project:
    values = to_values(payload, session)
    if payload.display_order is None:
        values["display_order"] = crud.get_row(
            session, Project, project_id
        ).display_order
    return crud.update_row(session, Project, project_id, values)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminRequired],
)
def delete_project(project_id: int, session: Db) -> Response:
    row = crud.get_row(session, Project, project_id)
    stored_image = row.image_filename
    crud.delete_row(session, Project, project_id)
    delete_upload(stored_image)  # otherwise the file is orphaned on disk
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/image", response_model=ImageOut, dependencies=[AdminRequired]
)
def upload_project_image(
    project_id: int,
    session: Db,
    file: Annotated[UploadFile, File()],
) -> ImageOut:
    row = crud.get_row(session, Project, project_id)
    previous = row.image_filename

    stored_name = save_image(file, prefix=f"project{project_id}")
    row.image_filename = stored_name
    session.commit()
    delete_upload(previous)  # replace, do not accumulate

    url = public_url(stored_name)
    assert url is not None  # stored_name is non-empty here
    return ImageOut(image_url=url)


@router.delete(
    "/{project_id}/image",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminRequired],
)
def delete_project_image(project_id: int, session: Db) -> Response:
    row = crud.get_row(session, Project, project_id)
    previous = row.image_filename
    row.image_filename = None
    session.commit()
    delete_upload(previous)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
