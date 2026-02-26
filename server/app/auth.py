"""JWT verification using Supabase JWT secret."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

security = HTTPBearer(auto_error=False)


class JWTClaims(BaseModel):
    """Decoded JWT claims (Supabase-style)."""

    sub: str
    email: str | None = None
    role: str | None = None
    aud: str | None = None


def verify_jwt(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> JWTClaims:
    """Verify JWT from Authorization header and return claims."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return JWTClaims(
            sub=payload.get("sub", ""),
            email=payload.get("email"),
            role=payload.get("role"),
            aud=payload.get("aud"),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
