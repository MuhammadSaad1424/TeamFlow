from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import logging

from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.utils.exceptions import NotFoundException, ValidationException
from app.core.security import hash_password

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management."""
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(
            select(User).where(User.id == user_id).where(User.deleted_at.is_(None))
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_user_by_github_id(db: AsyncSession, github_id: int) -> Optional[User]:
        """Get user by GitHub ID."""
        result = await db.execute(
            select(User).where(User.github_id == github_id).where(User.deleted_at.is_(None))
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User).where(User.email == email).where(User.deleted_at.is_(None))
        )
        return result.scalars().first()
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: dict) -> User:
        """Create new user."""
        # Check if user already exists
        existing = await UserService.get_user_by_github_id(db, user_data["github_id"])
        if existing:
            raise ValidationException("User with this GitHub account already exists")
        
        # Create user
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"New user created: {user.id} ({user.github_username})")
        return user
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: UUID, user_update: UserUpdate) -> User:
        """Update user information."""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User updated: {user_id}")
        return user
    
    @staticmethod
    async def update_github_tokens(
        db: AsyncSession,
        user_id: UUID,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> User:
        """Update GitHub tokens for user."""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        user.github_access_token = access_token
        if refresh_token:
            user.github_refresh_token = refresh_token
        if expires_at:
            user.github_token_expires_at = expires_at
        
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: UUID) -> User:
        """Update last login time."""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        user.last_login_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: UUID) -> None:
        """Soft delete user."""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        await db.commit()
        
        logger.info(f"User deleted: {user_id}")
    
    @staticmethod
    async def get_user_subscription_status(db: AsyncSession, user_id: UUID) -> dict:
        """Get user subscription status."""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        now = datetime.utcnow()
        is_active = user.subscription_tier != "free" and (
            user.subscription_expires_at is None or
            user.subscription_expires_at > now
        )
        
        return {
            "tier": user.subscription_tier,
            "is_active": is_active,
            "expires_at": user.subscription_expires_at,
        }
