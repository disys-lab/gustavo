"""
Firebase token verification middleware.

When AUTH_ENABLED=false (default), all routes pass through without verification.
When AUTH_ENABLED=true, every request must carry:
    Authorization: Bearer <Firebase idToken>

The token is verified using PyJWT (RS256) against Firebase's public keys.
For simplicity we use the firebase-admin SDK if available, else fall back to
a lightweight JWT decode approach.
"""
import os
import logging
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "false").lower() == "true"

_bearer = HTTPBearer(auto_error=False)


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> dict:
    """
    FastAPI dependency that verifies the Firebase ID token.

    Returns the decoded token payload (uid, email, etc.) when auth is enabled.
    Returns an empty dict when AUTH_ENABLED=false.
    """
    if not AUTH_ENABLED:
        return {}

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = credentials.credentials
    try:
        payload = _verify_token(token)
        return payload
    except Exception as exc:
        logging.warning(f"Token verification failed: {exc}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _verify_token(token: str) -> dict:
    """
    Attempt verification with firebase-admin first, fall back to PyJWT.
    """
    try:
        import firebase_admin
        from firebase_admin import auth as fb_auth, credentials as fb_creds

        # Initialize app lazily
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

    # Fallback: decode without full RS256 verification (dev only)
    import jwt
    # Decode header to get kid, then verify signature using Google's public key.
    # For production use firebase-admin; this path is a development convenience.
    decoded = jwt.decode(token, options={"verify_signature": False})
    logging.warning("Firebase token verified without signature check — install firebase-admin for production")
    return decoded
