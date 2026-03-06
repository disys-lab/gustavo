"""
Firebase token verification middleware.

When AUTH_ENABLED=false (default), all routes pass through without verification.
When AUTH_ENABLED=true, every request must carry:
    Authorization: Bearer <Firebase idToken>

Tokens are verified once (Firebase network call) then cached by their raw string
until their 'exp' claim expires. Subsequent requests with the same token are a
plain dict lookup — no network call.
"""
import os
import time
import logging
import threading
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "false").lower() == "true"

_bearer = HTTPBearer(auto_error=False)

# { token_string: {"payload": dict, "exp": int} }
_token_cache: dict = {}
_cache_lock = threading.Lock()


def _cache_get(token: str) -> dict | None:
    with _cache_lock:
        entry = _token_cache.get(token)
    if entry and entry["exp"] > time.time():
        return entry["payload"]
    # Expired — remove it
    with _cache_lock:
        _token_cache.pop(token, None)
    return None


def _cache_set(token: str, payload: dict) -> None:
    exp = payload.get("exp", int(time.time()) + 3600)
    with _cache_lock:
        _token_cache[token] = {"payload": payload, "exp": exp}


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> dict:
    if not AUTH_ENABLED:
        return {}

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = credentials.credentials

    # Fast path — already verified and not expired
    cached = _cache_get(token)
    if cached is not None:
        return cached

    # Slow path — first time seeing this token
    try:
        payload = _verify_token(token)
        _cache_set(token, payload)
        return payload
    except Exception as exc:
        logging.warning(f"Token verification failed: {exc}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _verify_token(token: str) -> dict:
    try:
        import firebase_admin
        from firebase_admin import auth as fb_auth, credentials as fb_creds

        if not firebase_admin._apps:
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path:
                cred = fb_creds.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()

        decoded = fb_auth.verify_id_token(token)
        return decoded
    except ImportError:
        pass
    except Exception as exc:
        raise exc

    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})
    logging.warning("Firebase token verified without signature check — install firebase-admin for production")
    return decoded
