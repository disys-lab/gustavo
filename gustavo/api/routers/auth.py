"""
/api/auth — Authentication.

GET  /api/auth/status → which login mode(s) are available.
POST /api/auth/login  → the one unified login endpoint. Body: {"credential": "identifier:secret"}.
                         Both the break-glass admin and every Nebula-backed
                         db user log in through this single field — see
                         nebula_auth.py / auth.py for how the two are told apart.
POST /api/auth/token  → optional Firebase/AUTH_ENDPOINT bridge (only meaningful
                         when AUTH_ENDPOINT is configured). A successful Firebase
                         login is treated as the platform admin — no per-user
                         Firebase identity bridging yet.
"""
import logging
import os

import requests
from fastapi import APIRouter
from pydantic import BaseModel

from gustavo.api import config_store, nebula_auth
from gustavo.api.session import Session, create_session_token

router = APIRouter()

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
AUTH_ENDPOINT = os.environ.get("AUTH_ENDPOINT", "")
CUSTOM_TOKEN_URL = os.environ.get(
    "CUSTOM_TOKEN_URL",
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken",
)
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "false").lower() in ("1", "true", "yes", "on")


class LoginRequest(BaseModel):
    credential: str


class TokenRequest(BaseModel):
    user_id: str
    user_token: str


def _admin_session() -> Session:
    """
    Build the break-glass platform-admin `Session`, from `NEBULA_USERNAME`/`NEBULA_PASSWORD`.

    Returns
    -------
    Session
        `user_type="local"`, `is_admin=True`.
    """
    cfg = config_store.get()
    return Session(
        username=cfg.get("NEBULA_USERNAME", "nebula"),
        user_type="local",
        is_admin=True,
        nebula_secret=cfg.get("NEBULA_PASSWORD", "nebula"),
    )


def _session_response(session: Session) -> dict:
    """
    Build the standard login-success response for `session`: a signed token plus display info.

    Parameters
    ----------
    session : Session
        The session to mint a token for.

    Returns
    -------
    dict
        ``{"error": False, "response": {"token": ..., "username": ...,
        "is_admin": ..., "groups": [...]}}``.

    Notes
    -----
    `groups` is only looked up for `user_type == "db"` (real Nebula
    users). The break-glass admin (`user_type == "local"`) isn't a
    real Nebula identity and doesn't need group membership: `is_admin`
    already bypasses every grant check this is used for (see e.g.
    `device_groups.py`'s `_require_dg_access`), so an empty list here
    is correct, not a gap.
    """
    groups = nebula_auth.user_groups(config_store.get(), session.username) if session.user_type == "db" else []
    return {
        "error": False,
        "response": {
            "token": create_session_token(session),
            "username": session.username,
            "is_admin": session.is_admin,
            "groups": groups,
        },
    }


@router.get("/status")
async def auth_status():
    """
    Which login mode(s) the frontend should offer.

    Returns
    -------
    dict
        ``{"auth_enabled": bool, "nebula_enabled": True,
        "firebase_enabled": bool}``.
    """
    return {
        "auth_enabled": AUTH_ENABLED,
        "nebula_enabled": True,
        "firebase_enabled": bool(AUTH_ENDPOINT),
    }


@router.post("/login")
async def login(req: LoginRequest):
    """
    Single unified login endpoint.

    Parameters
    ----------
    req : LoginRequest
        `credential`, formatted `"identifier:secret"`.

    Returns
    -------
    dict
        `_session_response`'s shape on success, or
        ``{"error": True, "response": <reason>}`` if `credential`
        isn't `"identifier:secret"`-shaped or the credentials don't
        verify.

    Notes
    -----
    - `identifier:secret == NEBULA_USERNAME:NEBULA_PASSWORD` (env
      vars, hard-checked, no Nebula reachability required) -> the
      break-glass admin session.
    - Otherwise, `identifier` is a claimed Nebula username and
      `secret` is that user's Nebula password (== their token, see
      `users.py`) -> verified via Nebula Basic auth, which is
      identity-bound (checked against that specific user's own stored
      hash), unlike Bearer/token verification.
    """
    if ":" not in req.credential:
        return {"error": True, "response": "Invalid credential format"}

    identifier, secret = req.credential.split(":", 1)
    cfg = config_store.get()
    session, error = nebula_auth.resolve_basic_credentials(cfg, identifier, secret)
    if error:
        return {"error": True, "response": error}
    return _session_response(session)


@router.post("/token")
async def get_token(req: TokenRequest):
    """
    Optional Firebase/AUTH_ENDPOINT login bridge.

    1. Exchange `user_id` + `user_token` for a Firebase custom token
       via `AUTH_ENDPOINT`.
    2. Exchange the custom token for a Firebase `idToken`.

    Parameters
    ----------
    req : TokenRequest
        `user_id`, `user_token`.

    Returns
    -------
    dict
        `_session_response`'s shape on success, or
        ``{"error": True, "response": <reason>}`` on any failure
        (endpoint/key not configured, either exchange step failing).
        If `AUTH_ENABLED` is `False`, always succeeds immediately
        without contacting `AUTH_ENDPOINT` at all.

    Notes
    -----
    A successful exchange is treated purely as a credential check - on
    success this mints a Gustavo session for the platform admin
    identity, same response shape as `/login`. There's no per-user
    Firebase identity bridging yet, so the Firebase `idToken` itself
    is discarded after step 2 confirms it exists.
    """
    if not AUTH_ENABLED:
        return _session_response(_admin_session())

    if not AUTH_ENDPOINT:
        logging.error("AUTH_ENDPOINT is not set")
        return {"error": True, "response": "AUTH_ENDPOINT is not configured on the server"}

    if not FIREBASE_API_KEY:
        logging.error("FIREBASE_API_KEY is not set")
        return {"error": True, "response": "FIREBASE_API_KEY is not configured on the server"}

    try:
        step1 = requests.post(
            f"{AUTH_ENDPOINT}/getAuthToken",
            json={"user_id": req.user_id, "user_token": req.user_token},
            headers={"Content-type": "application/json"},
            timeout=10,
        )
        if step1.status_code != 200:
            logging.warning(f"AUTH_ENDPOINT returned {step1.status_code}: {step1.text}")
            return {"error": True, "response": "Authentication failed. Please check your credentials."}

        firebase_token = step1.json().get("firebase_token")
        if not firebase_token:
            logging.warning("AUTH_ENDPOINT response missing firebase_token")
            return {"error": True, "response": "Failed to retrieve Firebase token from auth endpoint."}

        step2 = requests.post(
            f"{CUSTOM_TOKEN_URL}?key={FIREBASE_API_KEY}",
            json={"token": firebase_token, "returnSecureToken": True},
            timeout=10,
        )
        if step2.status_code != 200:
            logging.warning(f"Firebase custom token exchange failed: {step2.text}")
            return {"error": True, "response": "Failed to exchange custom token for ID token."}

        if not step2.json().get("idToken"):
            return {"error": True, "response": "No ID token returned by Firebase."}

        return _session_response(_admin_session())

    except Exception as exc:
        logging.error(f"Auth token exchange failed: {exc}")
        return {"error": True, "response": str(exc)}
