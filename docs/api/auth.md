# Authentication API

::: gustavo.api.routers.auth

---

## Endpoints

### `GET /api/auth/status`

Returns whether server-side authentication is currently enabled. Used by the frontend to determine whether to show the login page without a page rebuild.

**Response:**

```json
{ "auth_enabled": false }
```

This endpoint is always public (no token required).

---

### `POST /api/auth/token`

Exchange a User ID and User Token for a Firebase ID token. The ID token is then stored in the browser cookie and sent as `Authorization: Bearer` on subsequent requests.

**Request body:**

```json
{
  "user_id": "alice",
  "user_token": "my-secret-token"
}
```

**Success response:**

```json
{
  "error": false,
  "response": {
    "idToken": "eyJhbGciO...",
    "localId": "alice"
  }
}
```

**Error response:**

```json
{
  "error": true,
  "response": "Authentication failed. Please check your credentials."
}
```

**Authentication flow:**

```
Browser → POST /api/auth/token {user_id, user_token}
             │
             ▼
         FastAPI → POST {user_id, user_token} → AUTH_ENDPOINT/getAuthToken
             │                                       │
             │                              firebase_token (custom token)
             │
             ▼
         FastAPI → POST {token: firebase_token} → Firebase signInWithCustomToken
             │                                       │
             │                              idToken (JWT)
             │
             ▼
         Return {idToken, localId} to browser
             │
             ▼
         Browser stores idToken in localStorage + cookie
```

The Firebase API key (`FIREBASE_API_KEY`) and auth endpoint (`AUTH_ENDPOINT`) never leave the server.

When `AUTH_ENABLED=false`, the endpoint returns a synthetic `"auth-disabled"` token and the provided user ID without contacting Firebase.

---

## Auth dependency

::: gustavo.api.auth
