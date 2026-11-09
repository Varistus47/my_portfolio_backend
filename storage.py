"""Upload handling: validated, streamed to disk, stored under a random name.

The client-supplied filename is never used on disk. A uuid name kills both
path-traversal attempts and collisions; the original name is kept in the
database only for the resume download.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from config import (
    CHUNK_SIZE,
    IMAGE_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    PDF_EXTENSIONS,
    UPLOAD_DIR,
)

_MAX_MB = MAX_UPLOAD_BYTES // (1024 * 1024)


def save_upload(file: UploadFile, allowed: set[str], prefix: str) -> str:
    """Validate and stream `file` to the uploads directory.

    Returns the stored filename. Raises 400 on a disallowed extension and 413
    if the stream exceeds MAX_UPLOAD_BYTES (checked while writing, so a huge
    upload cannot be buffered in memory first).
    """
    extension = Path(file.filename or "").suffix.lower()
    if extension not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type '{extension or 'unknown'}'. "
                f"Allowed: {allowed_text}"
            ),
        )

    stored_name = f"{prefix}-{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / stored_name
    written = 0

    try:
        with destination.open("wb") as out:
            while chunk := file.file.read(CHUNK_SIZE):
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"File too large (max {_MAX_MB} MB)",
                    )
                out.write(chunk)
    except Exception:
        # Never leave a partial or orphaned file behind.
        destination.unlink(missing_ok=True)
        raise

    if written == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty"
        )

    return stored_name


def save_image(file: UploadFile, prefix: str) -> str:
    return save_upload(file, IMAGE_EXTENSIONS, prefix)


def save_pdf(file: UploadFile, prefix: str) -> str:
    return save_upload(file, PDF_EXTENSIONS, prefix)


def delete_upload(stored_name: str | None) -> None:
    """Remove a stored file. `Path(...).name` strips any traversal attempt."""
    if not stored_name:
        return
    (UPLOAD_DIR / Path(stored_name).name).unlink(missing_ok=True)


def upload_path(stored_name: str) -> Path:
    return UPLOAD_DIR / Path(stored_name).name


def public_url(stored_name: str | None) -> str | None:
    """Root-relative URL served by the /uploads static mount."""
    if not stored_name:
        return None
    return f"/uploads/{Path(stored_name).name}"
