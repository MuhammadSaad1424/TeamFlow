from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
import logging

from app.models import Repository, RepositoryFile, CodeChunk, Embedding
from app.schemas import RepositoryCreate
from app.utils.exceptions import NotFoundException, ForbiddenException
from app.utils.validators import validate_github_url, extract_github_info

logger = logging.getLogger(__name__)


class RepositoryService:
    """Service for repository management."""
    
    @staticmethod
    async def get_repository_by_id(db: AsyncSession, repo_id: UUID) -> Optional[Repository]:
        """Get repository by ID."""
        result = await db.execute(
            select(Repository).where(Repository.id == repo_id).where(Repository.deleted_at.is_(None))
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_user_repositories(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None
    ) -> tuple[List[Repository], int]:
        """Get user repositories with pagination."""
        query = select(Repository).where(
            and_(
                Repository.user_id == user_id,
                Repository.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(Repository.indexing_status == status)
        
        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        # Get paginated results
        query = query.order_by(desc(Repository.created_at))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        repositories = result.scalars().all()
        
        return repositories, total
    
    @staticmethod
    async def create_repository(
        db: AsyncSession,
        user_id: UUID,
        repo_data: dict
    ) -> Repository:
        """Create new repository."""
        # Validate GitHub URL
        if not validate_github_url(repo_data["repo_url"]):
            raise ValueError("Invalid GitHub URL format")
        
        # Check if already exists
        existing = await db.execute(
            select(Repository).where(
                and_(
                    Repository.user_id == user_id,
                    Repository.repo_url == repo_data["repo_url"],
                    Repository.deleted_at.is_(None)
                )
            )
        )
        
        if existing.scalars().first():
            raise ValueError("Repository already exists")
        
        # Create repository
        repository = Repository(
            user_id=user_id,
            **repo_data
        )
        
        db.add(repository)
        await db.commit()
        await db.refresh(repository)
        
        logger.info(f"Repository created: {repository.id} ({repository.repo_name})")
        return repository
    
    @staticmethod
    async def update_repository(
        db: AsyncSession,
        repo_id: UUID,
        update_data: dict
    ) -> Repository:
        """Update repository."""
        repo = await RepositoryService.get_repository_by_id(db, repo_id)
        if not repo:
            raise NotFoundException("Repository not found")
        
        for field, value in update_data.items():
            if value is not None:
                setattr(repo, field, value)
        
        repo.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(repo)
        
        logger.info(f"Repository updated: {repo_id}")
        return repo
    
    @staticmethod
    async def update_indexing_status(
        db: AsyncSession,
        repo_id: UUID,
        status: str,
        error_message: Optional[str] = None
    ) -> Repository:
        """Update repository indexing status."""
        repo = await RepositoryService.get_repository_by_id(db, repo_id)
        if not repo:
            raise NotFoundException("Repository not found")
        
        repo.indexing_status = status
        if status == "in_progress" and not repo.indexing_started_at:
            repo.indexing_started_at = datetime.utcnow()
        elif status == "completed":
            repo.indexing_completed_at = datetime.utcnow()
        
        if error_message:
            repo.indexing_error_message = error_message
        
        await db.commit()
        await db.refresh(repo)
        
        return repo
    
    @staticmethod
    async def get_repository_stats(db: AsyncSession, repo_id: UUID) -> dict:
        """Get repository statistics."""
        repo = await RepositoryService.get_repository_by_id(db, repo_id)
        if not repo:
            raise NotFoundException("Repository not found")
        
        # Count files
        files_result = await db.execute(
            select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
        )
        file_count = len(files_result.scalars().all())
        
        # Count chunks
        chunks_result = await db.execute(
            select(CodeChunk).where(CodeChunk.repository_id == repo_id)
        )
        chunk_count = len(chunks_result.scalars().all())
        
        # Count embeddings
        embeddings_result = await db.execute(
            select(Embedding).where(Embedding.repository_id == repo_id)
        )
        embedding_count = len(embeddings_result.scalars().all())
        
        return {
            "total_files": file_count,
            "total_chunks": chunk_count,
            "total_embeddings": embedding_count,
            "file_count": repo.file_count,
            "total_lines_of_code": repo.total_lines_of_code,
            "indexing_status": repo.indexing_status,
        }
    
    @staticmethod
    async def delete_repository(db: AsyncSession, repo_id: UUID) -> None:
        """Soft delete repository."""
        repo = await RepositoryService.get_repository_by_id(db, repo_id)
        if not repo:
            raise NotFoundException("Repository not found")
        
        repo.deleted_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Repository deleted: {repo_id}")
    
    @staticmethod
    async def verify_repository_access(
        db: AsyncSession,
        repo_id: UUID,
        user_id: UUID
    ) -> None:
        """Verify user has access to repository."""
        repo = await RepositoryService.get_repository_by_id(db, repo_id)
        if not repo:
            raise NotFoundException("Repository not found")
        
        if repo.user_id != user_id:
            raise ForbiddenException("You don't have access to this repository")
