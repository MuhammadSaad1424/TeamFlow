import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import CodeChunk, Embedding, Repository, RepositoryFile, RepositoryMetadata
from app.rag.chunking.code_chunker import CodeChunker
from app.rag.embeddings.embedding_service import (
    EmbeddingProcessor,
    GeminiEmbeddingModel,
    OpenAIEmbeddingModel,
    LocalEmbeddingModel,
)
from app.rag.ingestion.github_cloner import GitHubCloner
from app.rag.parsing.code_parser import CodeParser
from app.rag.retrieval.retrieval_engine import BM25Index
from app.rag.vector_store import ChromaDBStore, PineconeStore
from app.services.repository_service import RepositoryService
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)

_indexing_tasks: dict = {}


def get_vector_store():
    if settings.VECTOR_DB_TYPE == "pinecone" and settings.PINECONE_API_KEY:
        return PineconeStore(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT or "us-east-1",
            index_name=settings.PINECONE_INDEX_NAME,
        )
    return ChromaDBStore(path=settings.CHROMADB_PATH)


def get_embedding_processor() -> EmbeddingProcessor:
    if settings.GEMINI_API_KEY:
        model = GeminiEmbeddingModel(
            api_key=settings.GEMINI_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
    elif settings.OPENAI_API_KEY:
        model = OpenAIEmbeddingModel(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
    else:
        model = LocalEmbeddingModel()

    return EmbeddingProcessor(model)


class IndexingService:
    """Orchestrate repository cloning, parsing, chunking, and embedding."""

    @staticmethod
    async def start_indexing(
        db: AsyncSession,
        repo_id: UUID,
        user_github_token: str,
    ) -> dict:
        repo = await RepositoryService.get_repository_by_id(db, repo_id)
        if not repo:
            raise NotFoundException("Repository not found")

        if repo.indexing_status == "in_progress":
            return {"status": "in_progress", "message": "Indexing already in progress"}

        await RepositoryService.update_indexing_status(db, repo_id, "in_progress")

        task = asyncio.create_task(
            IndexingService._run_indexing(repo_id, repo.repo_url, user_github_token)
        )
        _indexing_tasks[str(repo_id)] = task

        return {"status": "in_progress", "message": "Indexing started"}

    @staticmethod
    async def get_index_status(db: AsyncSession, repo_id: UUID) -> dict:
        repo = await RepositoryService.get_repository_by_id(db, repo_id)
        if not repo:
            raise NotFoundException("Repository not found")

        stats = await RepositoryService.get_repository_stats(db, repo_id)
        return {
            "repository_id": str(repo_id),
            "status": repo.indexing_status,
            "embedding_status": repo.embedding_status,
            "progress": stats,
            "started_at": repo.indexing_started_at,
            "completed_at": repo.indexing_completed_at,
            "error": repo.indexing_error_message,
        }

    @staticmethod
    async def _run_indexing(repo_id: UUID, repo_url: str, access_token: str) -> None:
        from app.core.database import AsyncSessionLocal

        repo_path = None
        async with AsyncSessionLocal() as db:
            try:
                repo_path, gh_meta = await GitHubCloner.clone_repository(
                    repo_url, access_token
                )

                parser = CodeParser()
                chunker = CodeChunker()
                files = parser.scan_repository(repo_path)
                lang_info = parser.detect_languages(files)

                repo = await RepositoryService.get_repository_by_id(db, repo_id)
                repo.file_count = len(files)
                repo.total_lines_of_code = sum(f.get("line_count", 0) for f in files)
                repo.language_primary = lang_info["language_primary"]
                repo.languages_detected = lang_info["languages_detected"]
                for key, val in gh_meta.items():
                    if val is not None:
                        setattr(repo, key, val)
                await db.commit()

                all_chunks_for_bm25 = []
                vector_store = get_vector_store()
                embedding_processor = get_embedding_processor()

                for file_data in files:
                    db_file = RepositoryFile(
                        repository_id=repo_id,
                        file_path=file_data["file_path"],
                        file_name=file_data["file_name"],
                        file_extension=file_data["file_extension"],
                        file_size_bytes=file_data["file_size_bytes"],
                        language=file_data["language"],
                        is_binary=file_data["is_binary"],
                        is_test_file=file_data["is_test_file"],
                        is_documentation=file_data["is_documentation"],
                        line_count=file_data["line_count"],
                        function_count=file_data["function_count"],
                        class_count=file_data["class_count"],
                        import_count=file_data["import_count"],
                        parsed_at=datetime.utcnow(),
                    )
                    db.add(db_file)
                    await db.flush()

                    chunks = chunker.chunk_file(file_data)
                    chunk_records = []

                    for chunk_data in chunks:
                        db_chunk = CodeChunk(
                            repository_id=repo_id,
                            file_id=db_file.id,
                            chunk_index=chunk_data["chunk_index"],
                            chunk_type=chunk_data["chunk_type"],
                            raw_content=chunk_data["raw_content"],
                            cleaned_content=chunk_data["cleaned_content"],
                            content_hash=chunk_data["content_hash"],
                            language=chunk_data["language"],
                            start_line_number=chunk_data["start_line_number"],
                            end_line_number=chunk_data["end_line_number"],
                            entity_name=chunk_data.get("entity_name"),
                            entity_type=chunk_data.get("entity_type"),
                        )
                        db.add(db_chunk)
                        chunk_records.append((db_chunk, chunk_data))

                    await db.flush()

                    for db_chunk, chunk_data in chunk_records:
                        all_chunks_for_bm25.append({
                            "id": str(db_chunk.id),
                            "chunk_id": str(db_chunk.id),
                            "content": chunk_data["raw_content"],
                            "file_path": chunk_data["file_path"],
                            "entity_name": chunk_data.get("entity_name"),
                        })

                    if chunk_records and settings.GEMINI_API_KEY:
                        embed_inputs = [
                            {"content": cd["raw_content"], "metadata": cd["metadata"]}
                            for _, cd in chunk_records
                        ]
                        embedded = await embedding_processor.embed_chunks(embed_inputs)

                        vectors = []
                        for (db_chunk, chunk_data), emb in zip(chunk_records, embedded):
                            vector_id = str(uuid.uuid4())
                            db_chunk.is_embedded = True
                            db_chunk.embedding_id = vector_id

                            db.add(Embedding(
                                code_chunk_id=db_chunk.id,
                                repository_id=repo_id,
                                vector_id=vector_id,
                                embedding_model=settings.EMBEDDING_MODEL,
                                vector_dimension=emb["dimension"],
                                vector_db_provider=settings.VECTOR_DB_TYPE,
                                stored_at=datetime.utcnow(),
                            ))

                            vectors.append({
                                "id": vector_id,
                                "embedding": emb["embedding"],
                                "content": chunk_data["raw_content"],
                                "metadata": {
                                    "chunk_id": str(db_chunk.id),
                                    "file_path": chunk_data["file_path"],
                                    "entity_name": chunk_data.get("entity_name") or "",
                                    "start_line": chunk_data["start_line_number"],
                                    "end_line": chunk_data["end_line_number"],
                                },
                            })

                        if vectors:
                            await vector_store.add_vectors(vectors, str(repo_id))

                repo.embedding_status = "completed" if settings.GEMINI_API_KEY else "pending"
                repo.embedding_count = len(all_chunks_for_bm25)
                repo.indexing_status = "completed"
                repo.indexing_completed_at = datetime.utcnow()
                repo.last_analyzed_at = datetime.utcnow()

                metadata = RepositoryMetadata(
                    repository_id=repo_id,
                    architecture_summary=f"Repository with {len(files)} files across {len(lang_info['languages_detected'])} languages.",
                    main_modules=[f["file_path"].split("/")[0] for f in files[:20]],
                    external_dependencies=list({
                        imp.split()[1] if " " in imp else imp
                        for f in files for imp in f.get("imports", [])
                    })[:50],
                    code_statistics=lang_info.get("language_stats", {}),
                    last_analyzed_at=datetime.utcnow(),
                )
                db.add(metadata)
                await db.commit()

                BM25Index.get_instance(str(repo_id)).build(all_chunks_for_bm25)
                logger.info(f"Indexing completed for repo {repo_id}: {len(files)} files")

            except Exception as e:
                logger.error(f"Indexing failed for {repo_id}: {e}")
                await RepositoryService.update_indexing_status(
                    db, repo_id, "failed", str(e)
                )
            finally:
                if repo_path:
                    GitHubCloner.cleanup(repo_path)
                _indexing_tasks.pop(str(repo_id), None)
