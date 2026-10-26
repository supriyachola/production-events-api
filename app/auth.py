from datetime import datetime, timedelta, timezone
from hmac import compare_digest
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
    MANAGER_PASSWORD,
    MANAGER_USERNAME,
    SCANNER_PASSWORD,
    SCANNER_USERNAME,
)
from app.schemas import TokenRequest

bearer_scheme = HTTPBearer(auto_error=False)
USERS = {
    SCANNER_USERNAME: (SCANNER_PASSWORD, "scanner"),
    MANAGER_USERNAME: (MANAGER_PASSWORD, "manager"),
}


def create_access_token(username: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": username, "role": role, "exp": expires},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def authenticate(credentials: TokenRequest) -> str | None:
    user = USERS.get(credentials.username)
    if user is None or not compare_digest(user[0], credentials.password):
        return None
    return create_access_token(credentials.username, user[1])


def require_role(
    required_role: str,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> dict[str, str]:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid bearer token required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        claims = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError as exc:
        raise unauthorized from exc
    if claims.get("role") != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{required_role} role required",
        )
    return claims


def scanner_only(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> dict[str, str]:
    return require_role("scanner", credentials)


def manager_only(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> dict[str, str]:
    return require_role("manager", credentials)
