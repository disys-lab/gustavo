"""
Request authentication dependency.

When AUTH_ENABLED=false (default): all routes pass through as the platform
admin (no login required at all — matches today's dev-mode behaviour).
When AUTH_ENABLED=true: every request must carry a Gustavo session token
(minted at /api/auth/login or /api/auth/token), decoded here into a Session
carrying who's logged in, whether they're an admin, and the Nebula secret
needed to build a per-user Composer for this request.
"""
import os

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from gustavo.api import config_store
from gustavo.api.session import InvalidSession, Session, decode_session_token

AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "false").lower() in ("1", "true", "yes", "on")

_bearer = HTTPBearer(auto_error=False)


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> Session:
    if not AUTH_ENABLED:
        cfg = config_store.get()
        return Session(
            username=cfg.get("NEBULA_USERNAME", "nebula"),
            user_type="local",
            is_admin=True,
            nebula_secret=cfg.get("NEBULA_PASSWORD", "nebula"),
        )

    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    try:
        return decode_session_token(credentials.credentials)
    except InvalidSession:
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def require_admin(session: Session = Depends(verify_firebase_token)) -> Session:
    if not session.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return session
