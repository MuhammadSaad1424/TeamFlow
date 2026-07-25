import logging
from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RepositoryFile, RepositoryMetadata
from app.services.repository_service import RepositoryService
from app.utils.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class ArchitectureService:
    """Analyze repository architecture and dependencies."""

    @staticmethod
    async def get_architecture(db: AsyncSession, repo_id: UUID, user_id: UUID) -> dict:
        await RepositoryService.verify_repository_access(db, repo_id, user_id)
        repo = await RepositoryService.get_repository_by_id(db, repo_id)

        if repo.indexing_status != "completed":
            raise ValidationException("Repository must be indexed first")

        meta_result = await db.execute(
            select(RepositoryMetadata).where(RepositoryMetadata.repository_id == repo_id)
        )
        metadata = meta_result.scalars().first()

        files_result = await db.execute(
            select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
        )
        files = files_result.scalars().all()

        modules = defaultdict(lambda: {"files": 0, "lines": 0, "functions": 0})
        for f in files:
            module = f.file_path.split("/")[0] if "/" in f.file_path else "root"
            modules[module]["files"] += 1
            modules[module]["lines"] += f.line_count or 0
            modules[module]["functions"] += f.function_count or 0

        module_list = [
            {"name": name, **stats}
            for name, stats in sorted(modules.items(), key=lambda x: -x[1]["lines"])
        ]

        return {
            "repository_id": str(repo_id),
            "summary": metadata.architecture_summary if metadata else "",
            "modules": module_list,
            "services": metadata.key_services if metadata and metadata.key_services else [],
            "patterns_detected": metadata.design_patterns if metadata else [],
            "data_flow_diagram": ArchitectureService._generate_mermaid(module_list),
            "languages": repo.languages_detected or [],
            "total_files": repo.file_count,
            "total_loc": repo.total_lines_of_code,
        }

    @staticmethod
    async def get_dependencies(db: AsyncSession, repo_id: UUID, user_id: UUID) -> dict:
        await RepositoryService.verify_repository_access(db, repo_id, user_id)

        files_result = await db.execute(
            select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
        )
        files = files_result.scalars().all()

        internal_deps: dict = defaultdict(list)
        external_deps: set = set()
        module_interactions: list = []

        meta_result = await db.execute(
            select(RepositoryMetadata).where(RepositoryMetadata.repository_id == repo_id)
        )
        metadata = meta_result.scalars().first()
        if metadata and metadata.external_dependencies:
            external_deps = set(metadata.external_dependencies)

        for f in files:
            module = f.file_path.split("/")[0] if "/" in f.file_path else "root"
            internal_deps[module].append(f.file_path)

        return {
            "repository_id": str(repo_id),
            "external_dependencies": sorted(external_deps),
            "internal_modules": {k: len(v) for k, v in internal_deps.items()},
            "module_interactions": module_interactions,
            "import_graph": ArchitectureService._build_import_graph(files),
        }

    @staticmethod
    def _generate_mermaid(modules: list) -> str:
        lines = ["graph TD"]
        for i, mod in enumerate(modules[:10]):
            node_id = f"M{i}"
            lines.append(f'    {node_id}["{mod["name"]}<br/>{mod["files"]} files"]')
            if i > 0:
                lines.append(f"    M{i-1} --> {node_id}")
        return "\n".join(lines)

    @staticmethod
    def _build_import_graph(files) -> list:
        edges = []
        for f in files[:30]:
            if f.language:
                edges.append({
                    "file": f.file_path,
                    "import_count": f.import_count or 0,
                    "language": f.language,
                })
        return edges
