"""Single shared-password admin auth with a stateless signed token.

Why stateless: an in-memory token set would be wiped on every
`uvicorn --reload` restart, which happens on each file save during development
and would log the admin out constantly. Instead the token carries its own
expiry and an HMAC over that expiry, so no server-side session state exists.

Token format: "<expiry_epoch>.<hex_hmac_sha256>"
"""

import hashlib
import hmac
import secrets
import time
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from config import ADMIN_PASSWORD, TOKEN_SECRET, TOKEN_TTL_SECONDS


def check_password(candidate: str) -> bool:
    """Constant-time comparison, so timing does not leak the password."""
    return secrets.compare_digest(
        candidate.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8")
    )


def _sign(expiry: int) -> str:
    return hmac.new(
        TOKEN_SECRET.encode("utf-8"),
        str(expiry).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def make_token() -> str:
    expiry = int(time.time()) + TOKEN_TTL_SECONDS
    return f"{expiry}.{_sign(expiry)}"


def verify_token(token: str | None) -> bool:
    if not token:
        return False
    expiry_text, _, signature = token.partition(".")
    if not signature:
        return False
    try:
        expiry = int(expiry_text)
    except ValueError:
        return False
    if expiry < int(time.time()):
        return False
    return secrets.compare_digest(signature, _sign(expiry))


def require_admin(
    x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> None:
    """Dependency guarding every mutating route. Public GETs do not use it."""
    if not verify_token(x_admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token",
        )


# Attach to a route with: dependencies=[AdminRequired]
AdminRequired = Depends(require_admin)
