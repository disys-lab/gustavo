"""
Request authentication dependency.

When AUTH_ENABLED=false (default): all routes pass through without any check.
When AUTH_ENABLED=true: every request must carry a non-empty Bearer token.

The token is obtained once at login via the two-step Firebase exchange
(matching AuthTokenHandler.py). We trust its presence here — no
cryptographic re-verification per request, mirroring the Streamlit behaviour.
"""
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "false").lower() in ("1", "true", "yes", "on")

_bearer = HTTPBearer(auto_error=False)


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> dict:
    if not AUTH_ENABLED:
        return {}

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Empty token")

    # Token presence is sufficient — it was validated by Firebase at login time.
    return {"token": credentials.credentials}
