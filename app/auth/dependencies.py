from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.auth.jwt import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


async def get_token_from_request(request: Request) -> str | None:
    """Extract token from Authorization header or X-API-Key header."""
    # Check Authorization header first
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]

    # Check X-API-Key header
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return api_key

    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve current user from JWT token or API key."""
    token = None

    if credentials:
        token = credentials.credentials
    else:
        token = await get_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token or X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try JWT token first
    payload = decode_access_token(token)
    if payload:
        user_id = int(payload.get("sub", 0))
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active:
            return user

    # Try API key
    user = db.query(User).filter(User.api_key == token, User.is_active == True).first()
    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require any authenticated user."""
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
