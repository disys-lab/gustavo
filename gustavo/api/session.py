"""
Gustavo session tokens.

A session is a signed JWT the browser holds in place of a raw Nebula
credential. It carries just enough to rebuild a per-user Nebula Composer on
each request: who's logged in, whether they're an admin, and their Nebula
secret (a password for the break-glass admin, a Nebula token for everyone
else), Fernet-encrypted so it never sits in the JWT payload in plaintext.

GUSTAVO_SESSION_SECRET is the single root secret. Two independent keys are
HKDF-derived from it: one for JWT signing, one for Fernet encryption — so the
same root secret is never reused across purposes.
"""
import base64
import logging
import os
import secrets as _secrets
import time
from dataclasses import dataclass
from typing import Literal

import jwt
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

SESSION_TTL_SECONDS = int(os.environ.get("GUSTAVO_SESSION_TTL", str(12 * 3600)))

_JWT_ALGORITHM = "HS256"


def _load_root_secret() -> bytes:
    configured = os.environ.get("GUSTAVO_SESSION_SECRET", "")
    if configured:
        return configured.encode("utf-8")
    logging.warning(
        "GUSTAVO_SESSION_SECRET is not set — generating a random secret for this "
        "process. Every session will be invalidated on restart. Set "
        "GUSTAVO_SESSION_SECRET in docker-compose.yml for production deployments."
    )
    return _secrets.token_bytes(32)


def _derive_key(root: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(root)


_ROOT_SECRET = _load_root_secret()
_JWT_SIGNING_KEY = _derive_key(_ROOT_SECRET, b"gustavo-session-jwt")
_FERNET = Fernet(base64.urlsafe_b64encode(_derive_key(_ROOT_SECRET, b"gustavo-session-fernet")))


@dataclass
class Session:
    username: str
    user_type: Literal["local", "db"]
    is_admin: bool
    # Password for user_type="local" (the break-glass admin), a Nebula
    # token for user_type="db" (everyone else).
    nebula_secret: str


class InvalidSession(Exception):
    pass


def create_session_token(session: Session) -> str:
    claims = {
        "username": session.username,
        "user_type": session.user_type,
        "is_admin": session.is_admin,
        "enc_secret": _FERNET.encrypt(session.nebula_secret.encode("utf-8")).decode("utf-8"),
        "exp": int(time.time()) + SESSION_TTL_SECONDS,
    }
    return jwt.encode(claims, _JWT_SIGNING_KEY, algorithm=_JWT_ALGORITHM)


def decode_session_token(token: str) -> Session:
    try:
        claims = jwt.decode(token, _JWT_SIGNING_KEY, algorithms=[_JWT_ALGORITHM])
        nebula_secret = _FERNET.decrypt(claims["enc_secret"].encode("utf-8")).decode("utf-8")
        return Session(
            username=claims["username"],
            user_type=claims["user_type"],
            is_admin=claims["is_admin"],
            nebula_secret=nebula_secret,
        )
    except (jwt.PyJWTError, InvalidToken, KeyError) as exc:
        raise InvalidSession(str(exc)) from exc
