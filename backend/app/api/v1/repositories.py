from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas import RepositoryCreate, RepositoryResponse
from app.services.indexing_service import IndexingService
from app.services.repository_service import RepositoryService
from app.utils.exceptions import create_paginated_response, create_response
from app.utils.validators import extract_github_info

router = APIRouter()


@router.post("")
async def create_repository(
    body: RepositoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a GitHub repository for analysis."""
    github_url = body.github_url.rstrip("/")
    info = extract_github_info(github_url)
    if not info:
        return create_response(success=False, status_code=422, message="Invalid GitHub URL")

    owner, repo_name = info
    repo_data = {
        "repo_name": body.name or repo_name,
        "repo_url": github_url,
        "description": body.description,
    }

    try:
        repository = await RepositoryService.create_repository(db, current_user.id, repo_data)
    except ValueError as e:
        return create_response(success=False, status_code=400, message=str(e))

    return create_response(
        success=True,
        status_code=201,
        message="Repository added",
        data={"repository": RepositoryResponse.model_validate(repository).model_dump(mode="json")},
    )


@router.get("")
async def list_repositories(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user repositories."""
    skip = (page - 1) * limit
    repos, total = await RepositoryService.get_user_repositories(
        db, current_user.id, skip=skip, limit=limit, status=status
    )
    items = [RepositoryResponse.model_validate(r).model_dump(mode="json") for r in repos]
    return create_response(
        success=True,
        status_code=200,
        data=create_paginated_response(items, total, page, limit),
    )


@router.get("/{repo_id}")
async def get_repository(
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get repository details."""
    await RepositoryService.verify_repository_access(db, repo_id, current_user.id)
    repo = await RepositoryService.get_repository_by_id(db, repo_id)
    stats = await RepositoryService.get_repository_stats(db, repo_id)
    data = RepositoryResponse.model_validate(repo).model_dump(mode="json")
    data["stats"] = stats
    return create_response(success=True, status_code=200, data=data)


@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a repository."""
    await RepositoryService.verify_repository_access(db, repo_id, current_user.id)
    await RepositoryService.delete_repository(db, repo_id)
    return create_response(success=True, status_code=200, message="Repository deleted")


@router.post("/{repo_id}/index")
async def index_repository(
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start indexing a repository."""
    await RepositoryService.verify_repository_access(db, repo_id, current_user.id)
    result = await IndexingService.start_indexing(
        db, repo_id, current_user.github_access_token
    )
    return create_response(success=True, status_code=202, message="Indexing started", data=result)


@router.get("/{repo_id}/index/status")
async def get_index_status(
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get repository indexing status."""
    await RepositoryService.verify_repository_access(db, repo_id, current_user.id)
    status = await IndexingService.get_index_status(db, repo_id)
    return create_response(success=True, status_code=200, data=status)
