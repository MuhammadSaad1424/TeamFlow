"""Create a test user and generate JWT token for local testing."""
import asyncio
import sys
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, '.')

from app.models import Base, User
from app.core.security import create_access_token
from app.core.config import settings


async def setup_test_user():
    """Create test user and generate token."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL)
    
    # Create async session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create a test user
        test_user = User(
            id=uuid4(),
            github_id=123456,
            github_username="testuser",
            email="test@example.com",
            display_name="Test User",
            avatar_url="https://avatars.githubusercontent.com/u/123456",
            bio="Test user for local development",
            subscription_tier="free",
            is_active=True,
            github_access_token="test_token_for_local_development",  # Required field
        )
        
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        # Generate JWT token
        token = create_access_token({"sub": str(test_user.id)})
        
        print(f"✅ Test user created:")
        print(f"   User ID: {test_user.id}")
        print(f"   Username: {test_user.github_username}")
        print(f"   Email: {test_user.email}")
        print(f"\n🔐 JWT Token (use in Authorization header):")
        print(f"   Bearer {token}")
        print(f"\n📝 Example curl command:")
        print(f'   curl -X POST http://localhost:8000/api/v1/repositories \\')
        print(f'     -H "Authorization: Bearer {token}" \\')
        print(f'     -H "Content-Type: application/json" \\')
        print(f'     -d \'{{"github_url": "https://github.com/owner/repo"}}\'')


if __name__ == "__main__":
    asyncio.run(setup_test_user())
