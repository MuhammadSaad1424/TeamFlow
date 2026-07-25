from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.services.documentation_service import DocumentationService
from app.utils.exceptions import create_response

router = APIRouter()


@router.post("/{repo_id}/generate")
async def generate_documentation(
    repo_id: UUID,
    doc_type: str = Query("readme", regex="^(readme|api|technical|developer_guide)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate documentation for a repository."""
    result = await DocumentationService.generate(
        db, repo_id, current_user.id, doc_type
    )
    return create_response(success=True, status_code=200, data=result)
