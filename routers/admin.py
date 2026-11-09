"""Admin login and session check."""

from fastapi import APIRouter, HTTPException, status

from auth import AdminRequired, check_password, make_token
from config import TOKEN_TTL_SECONDS
from schemas import LoginIn, SessionOut, TokenOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn) -> TokenOut:
    if not check_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
        )
    return TokenOut(token=make_token(), expires_in=TOKEN_TTL_SECONDS)


@router.get("/session", response_model=SessionOut, dependencies=[AdminRequired])
def session() -> SessionOut:
    """200 only when the X-Admin-Token header holds a valid, unexpired token."""
    return SessionOut(valid=True)
