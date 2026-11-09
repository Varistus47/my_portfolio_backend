"""Profile (singleton), photo upload, resume upload and resume download."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth import AdminRequired
from database import get_db
from models import Profile
from schemas import PhotoOut, ProfileIn, ProfileOut, ResumeOut
from storage import delete_upload, public_url, save_image, save_pdf, upload_path

router = APIRouter(prefix="/api", tags=["profile"])

Db = Annotated[Session, Depends(get_db)]

RESUME_URL = "/api/resume"


def fetch_profile_row(session: Session) -> Profile:
    """The singleton always exists: init_db() inserts id = 1."""
    row = session.get(Profile, 1)
    if row is None:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile row is missing; restart the server to re-initialise.",
        )
    return row


# --------------------------------------------------------------------- profile


@router.get("/profile", response_model=ProfileOut)
def get_profile(session: Db) -> Profile:
    return fetch_profile_row(session)


@router.put("/profile", response_model=ProfileOut, dependencies=[AdminRequired])
def update_profile(payload: ProfileIn, session: Db) -> Profile:
    """Full replace of the text fields. Filenames are not settable here -
    they change only through the upload and delete endpoints below."""
    row = fetch_profile_row(session)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    session.commit()
    session.refresh(row)
    return row


# ----------------------------------------------------------------------- photo


@router.post("/profile/photo", response_model=PhotoOut, dependencies=[AdminRequired])
def upload_photo(session: Db, file: Annotated[UploadFile, File()]) -> PhotoOut:
    row = fetch_profile_row(session)
    previous = row.photo_filename

    stored_name = save_image(file, prefix="photo")
    row.photo_filename = stored_name
    session.commit()
    delete_upload(previous)  # replace, do not accumulate

    url = public_url(stored_name)
    assert url is not None
    return PhotoOut(photo_url=url)


@router.delete(
    "/profile/photo",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminRequired],
)
def delete_photo(session: Db) -> Response:
    row = fetch_profile_row(session)
    previous = row.photo_filename
    row.photo_filename = None
    session.commit()
    delete_upload(previous)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------- resume


@router.post(
    "/profile/resume", response_model=ResumeOut, dependencies=[AdminRequired]
)
def upload_resume(session: Db, file: Annotated[UploadFile, File()]) -> ResumeOut:
    row = fetch_profile_row(session)
    previous = row.resume_filename

    stored_name = save_pdf(file, prefix="resume")
    original = (file.filename or "resume.pdf").strip() or "resume.pdf"
    row.resume_filename = stored_name
    row.resume_original_name = original
    session.commit()
    delete_upload(previous)

    return ResumeOut(resume_url=RESUME_URL, resume_original_name=original)


@router.delete(
    "/profile/resume",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminRequired],
)
def delete_resume(session: Db) -> Response:
    row = fetch_profile_row(session)
    previous = row.resume_filename
    row.resume_filename = None
    row.resume_original_name = None
    session.commit()
    delete_upload(previous)  # the file itself must go, not just the column
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _resume_response(session: Session, disposition: str) -> FileResponse:
    row = fetch_profile_row(session)
    stored_name = row.resume_filename
    if not stored_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No resume uploaded"
        )
    path = upload_path(stored_name)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file is missing from the server; re-upload it.",
        )
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=row.resume_download_name,
        content_disposition_type=disposition,
    )


@router.get("/resume")
def download_resume(session: Db) -> FileResponse:
    """Public download. Starlette handles RFC 5987 filename encoding."""
    return _resume_response(session, "attachment")


@router.get("/resume/inline")
def view_resume(session: Db) -> FileResponse:
    """Same bytes, rendered in the browser's PDF viewer instead of downloaded."""
    return _resume_response(session, "inline")
