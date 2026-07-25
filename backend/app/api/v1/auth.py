from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import User
from app.schemas import AuthResponse, RefreshTokenRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.utils.exceptions import create_response

router = APIRouter()


@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth authorization."""
    if not settings.GITHUB_CLIENT_ID:
        return create_response(
            success=False,
            status_code=400,
            message="GitHub OAuth not configured. Use POST /auth/dev-login in debug mode.",
        )
    url = AuthService.get_github_auth_url()
    return RedirectResponse(url=url)


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback and redirect to frontend."""
    result = await AuthService.exchange_github_code(db, code)
    user = result.pop("user")
    params = urlencode({
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "username": user.github_username,
        "email": user.email,
        "avatar_url": user.avatar_url or "",
        "user_id": str(user.id),
    })
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?{params}")


@router.post("/refresh")
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    tokens = await AuthService.refresh_access_token(db, body.refresh_token)
    return create_response(
        success=True,
        status_code=200,
        message="Token refreshed",
        data=tokens,
    )


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout and revoke session."""
    await AuthService.logout(db, current_user.id)
    return create_response(success=True, status_code=200, message="Logged out")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return create_response(
        success=True,
        status_code=200,
        data={"user": UserResponse.model_validate(current_user).model_dump()},
    )


@router.post("/dev-login")
async def dev_login(db: AsyncSession = Depends(get_db)):
    """Development login without GitHub OAuth."""
    result = await AuthService.dev_login(db)
    user = result.pop("user")
    return create_response(
        success=True,
        status_code=200,
        message="Dev login successful",
        data={
            **result,
            "user": UserResponse.model_validate(user).model_dump(),
        },
    )
