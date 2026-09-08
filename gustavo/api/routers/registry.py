"""
/api/registry — Docker registry access checks, for nginx's auth_request.

GET|HEAD|PUT|POST|PATCH|DELETE /api/registry/authorize → 200 = allow, 401 = deny

The registry-proxy nginx container (see cypress-ai:~/gustavo/registry-proxy)
fires this as an auth_request sub-request for every /v2/... call it
receives, forwarding the original Authorization header automatically. This
replaces a static htpasswd file with a live check against Nebula's own
users: any request carrying a valid Nebula username:secret (Basic auth) or
a Gustavo session Bearer token is allowed through; anything else gets a
401 before the real registry ever sees the request.

All HTTP methods are accepted (not just GET) because auth_request forwards
the *original* client method through - a docker push arrives as
PUT/PATCH/POST/DELETE, not GET, and the response's body is irrelevant
either way: nginx only looks at the status code.

Tier 1 only (this endpoint): identity is enough, no per-repo check. A
Tier 2 (per-repo, ro/rw-aware) version would additionally read the
X-Original-URI/X-Original-Method headers nginx forwards and cross-check
compute_permissions(cfg, session.username)["apps"] for the requested repo.
"""
from fastapi import APIRouter, Depends

from gustavo.api.auth import verify_session_or_basic
from gustavo.api.session import Session

router = APIRouter()


@router.api_route("/authorize", methods=["GET", "HEAD", "PUT", "POST", "PATCH", "DELETE"])
async def authorize_registry(session: Session = Depends(verify_session_or_basic)):
    """
    Return 200 if the request carries valid Nebula/Gustavo credentials, else 401 (raised inside the dependency).

    Parameters
    ----------
    session : Session
        The authenticated caller, via `verify_session_or_basic`. Not
        otherwise inspected - reaching this line at all means auth
        succeeded (see module docstring: Tier 1 only, no per-repo
        check).

    Returns
    -------
    dict
        ``{"error": False, "response": "ok"}``. The body is ignored
        by nginx; only the HTTP status code matters.
    """
    return {"error": False, "response": "ok"}
