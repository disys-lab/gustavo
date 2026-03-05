"""
/api/auth — Authentication proxy.

POST /api/auth/token  → exchange user_id + user_token for a Firebase idToken.

Flow (mirrors AuthTokenHandler.py / Home.py):
  1. POST {user_id, user_token} → AUTH_ENDPOINT/getAuthToken → firebase_token (custom token)
  2. POST {token: firebase_token} → Firebase signInWithCustomToken → idToken
  3. Return idToken to the browser (FIREBASE_API_KEY never leaves the server)
"""
import os
import logging
import requests
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
AUTH_ENDPOINT = os.environ.get("AUTH_ENDPOINT", "")
FIREBASE_CUSTOM_TOKEN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
)
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "false").lower() in ("1", "true", "yes", "on")


class TokenRequest(BaseModel):
    user_id: str
    user_token: str


@router.post("/token")
async def get_token(req: TokenRequest):
    """
    Two-step auth flow (mirrors Streamlit AuthTokenHandler):
      1. Exchange user_id + user_token for a Firebase custom token via AUTH_ENDPOINT.
      2. Exchange the custom token for a Firebase idToken.
    Returns the idToken for use in Authorization: Bearer headers.
    """
    if not AUTH_ENABLED:
        return {"error": False, "response": {"idToken": "auth-disabled", "localId": req.user_id}}

    if not AUTH_ENDPOINT:
        logging.error("AUTH_ENDPOINT is not set")
        return {"error": True, "response": "AUTH_ENDPOINT is not configured on the server"}

    if not FIREBASE_API_KEY:
        logging.error("FIREBASE_API_KEY is not set")
        return {"error": True, "response": "FIREBASE_API_KEY is not configured on the server"}

    try:
        # Step 1: Get Firebase custom token from the auth endpoint
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

        # Step 2: Exchange custom token for idToken via Firebase REST API
        step2 = requests.post(
            f"{FIREBASE_CUSTOM_TOKEN_URL}?key={FIREBASE_API_KEY}",
            json={"token": firebase_token, "returnSecureToken": True},
            timeout=10,
        )
        if step2.status_code != 200:
            logging.warning(f"Firebase custom token exchange failed: {step2.text}")
            return {"error": True, "response": "Failed to exchange custom token for ID token."}

        id_token = step2.json().get("idToken")
        if not id_token:
            return {"error": True, "response": "No ID token returned by Firebase."}

        return {"error": False, "response": {"idToken": id_token, "localId": req.user_id}}

    except Exception as exc:
        logging.error(f"Auth token exchange failed: {exc}")
        return {"error": True, "response": str(exc)}
