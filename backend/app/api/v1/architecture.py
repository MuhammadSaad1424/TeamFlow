from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.services.architecture_service import ArchitectureService
from app.utils.exceptions import create_response

router = APIRouter()


@router.get("/{repo_id}")
async def get_architecture(
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get architecture analysis for a repository."""
    data = await ArchitectureService.get_architecture(db, repo_id, current_user.id)
    return create_response(success=True, status_code=200, data=data)


@router.get("/{repo_id}/dependencies")
async def get_dependencies(
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dependency analysis for a repository."""
    data = await ArchitectureService.get_dependencies(db, repo_id, current_user.id)
    return create_response(success=True, status_code=200, data=data)
