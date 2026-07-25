from typing import Optional
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User
from app.services.user_service import UserService
from app.utils.exceptions import NotAuthorizedException

security = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None),
) -> User:
    """Resolve the authenticated user from a Bearer token."""
    token = None
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]

    if not token:
        raise NotAuthorizedException("Authentication required")

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise NotAuthorizedException("Invalid or expired token")

    user = await UserService.get_user_by_id(db, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise NotAuthorizedException("User not found or inactive")

    return user


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Return the current user when a valid token is present."""
    if not credentials:
        return None
    try:
        return await get_current_user(db=db, credentials=credentials)
    except NotAuthorizedException:
        return None
