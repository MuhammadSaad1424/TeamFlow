from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models import Session, User
from app.services.user_service import UserService
from app.utils.exceptions import NotAuthorizedException, ValidationException

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"


class AuthService:
    """GitHub OAuth and JWT session management."""

    @staticmethod
    def get_github_auth_url(state: Optional[str] = None) -> str:
        if not settings.GITHUB_CLIENT_ID:
            raise ValidationException("GitHub OAuth is not configured")
        state = state or str(uuid4())
        return (
            f"{GITHUB_AUTHORIZE_URL}"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
            f"&scope=read:user user:email repo"
            f"&state={state}"
        )

    @staticmethod
    async def exchange_github_code(db: AsyncSession, code: str) -> dict:
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            raise ValidationException("GitHub OAuth is not configured")

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
            )
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise NotAuthorizedException("Failed to obtain GitHub access token")

            user_resp = await client.get(
                GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            github_user = user_resp.json()

        email = github_user.get("email") or f"{github_user['login']}@users.noreply.github.com"
        existing = await UserService.get_user_by_github_id(db, github_user["id"])

        if existing:
            user = await UserService.update_github_tokens(db, existing.id, access_token)
            user.github_username = github_user["login"]
            user.avatar_url = github_user.get("avatar_url")
            user.display_name = github_user.get("name") or github_user["login"]
            user.email = email
            await db.commit()
            await db.refresh(user)
        else:
            user = await UserService.create_user(
                db,
                {
                    "github_id": github_user["id"],
                    "github_username": github_user["login"],
                    "email": email,
                    "avatar_url": github_user.get("avatar_url"),
                    "display_name": github_user.get("name") or github_user["login"],
                    "bio": github_user.get("bio"),
                    "github_access_token": access_token,
                },
            )

        await UserService.update_last_login(db, user.id)
        tokens = await AuthService.create_session(db, user.id)
        return {**tokens, "user": user}

    @staticmethod
    async def create_session(db: AsyncSession, user_id: UUID) -> dict:
        access_token = create_access_token({"sub": str(user_id), "type": "access"})
        refresh_token = create_refresh_token({"sub": str(user_id), "type": "refresh"})

        session = Session(
            user_id=user_id,
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(session)
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise NotAuthorizedException("Invalid refresh token")

        user_id = UUID(payload["sub"])
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotAuthorizedException("User not found")

        access_token = create_access_token({"sub": str(user_id), "type": "access"})
        return {
            "access_token": access_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "token_type": "bearer",
        }

    @staticmethod
    async def logout(db: AsyncSession, user_id: UUID) -> None:
        from sqlalchemy import update

        await db.execute(
            update(Session)
            .where(Session.user_id == user_id, Session.is_active == True)
            .values(is_active=False, is_revoked=True, revoked_at=datetime.utcnow())
        )
        await db.commit()

    @staticmethod
    async def dev_login(db: AsyncSession) -> dict:
        """Development login when GitHub OAuth is not configured."""
        if settings.GITHUB_CLIENT_ID and not settings.DEBUG:
            raise ValidationException(
                "Dev login is only available in debug mode or when GitHub OAuth is not configured"
            )

        existing = await UserService.get_user_by_github_id(db, 0)
        if not existing:
            user = await UserService.create_user(
                db,
                {
                    "github_id": 0,
                    "github_username": "dev-user",
                    "email": "dev@teamflow.ai",
                    "display_name": "Dev User",
                    "avatar_url": "https://github.com/identicons/dev-user.png",
                    "github_access_token": "dev-token",
                },
            )
        else:
            user = existing

        tokens = await AuthService.create_session(db, user.id)
        return {**tokens, "user": user}
