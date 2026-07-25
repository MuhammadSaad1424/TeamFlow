import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import RepositoryFile, RepositoryMetadata
from app.rag.generation.response_generator import OpenAIProvider, ResponseGenerator
from app.services.repository_service import RepositoryService
from app.utils.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class DocumentationService:
    """Generate documentation from indexed repositories."""

    DOC_TYPES = {"readme", "api", "technical", "developer_guide"}

    @staticmethod
    async def generate(
        db: AsyncSession,
        repo_id: UUID,
        user_id: UUID,
        doc_type: str = "readme",
    ) -> dict:
        await RepositoryService.verify_repository_access(db, repo_id, user_id)
        repo = await RepositoryService.get_repository_by_id(db, repo_id)

        if repo.indexing_status != "completed":
            raise ValidationException("Repository must be indexed before generating docs")

        if doc_type not in DocumentationService.DOC_TYPES:
            raise ValidationException(f"Invalid doc type. Choose from: {DocumentationService.DOC_TYPES}")

        files_result = await db.execute(
            select(RepositoryFile)
            .where(RepositoryFile.repository_id == repo_id)
            .order_by(RepositoryFile.file_path)
            .limit(30)
        )
        files = files_result.scalars().all()

        file_summary = "\n".join(
            f"- {f.file_path} ({f.language}, {f.line_count} lines, {f.function_count} functions)"
            for f in files
        )

        prompts = {
            "readme": f"Generate a comprehensive README.md for the repository '{repo.repo_name}'. Include overview, setup, usage, and project structure.\n\nFiles:\n{file_summary}",
            "api": f"Generate API documentation for '{repo.repo_name}' based on these source files:\n{file_summary}",
            "technical": f"Generate technical documentation explaining the architecture and key components of '{repo.repo_name}':\n{file_summary}",
            "developer_guide": f"Generate a developer onboarding guide for '{repo.repo_name}':\n{file_summary}",
        }

        llm = OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
        generator = ResponseGenerator(llm)
        content = await generator.generate_response(
            prompts[doc_type], [], max_tokens=3000
        )

        meta_result = await db.execute(
            select(RepositoryMetadata).where(RepositoryMetadata.repository_id == repo_id)
        )
        metadata = meta_result.scalars().first()
        if metadata:
            field_map = {
                "readme": "auto_generated_readme",
                "api": "auto_generated_api_doc",
            }
            if doc_type in field_map:
                setattr(metadata, field_map[doc_type], content)
                await db.commit()

        return {
            "repository_id": str(repo_id),
            "doc_type": doc_type,
            "content": content,
            "generated_at": repo.last_analyzed_at,
        }
