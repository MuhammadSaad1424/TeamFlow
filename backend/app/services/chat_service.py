import logging
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Citation, CodeChunk, Conversation, Message, RepositoryFile
from app.rag.embeddings.embedding_service import EmbeddingProcessor, GeminiEmbeddingModel
from app.rag.generation.response_generator import (
    GeminiProvider,
    OpenAIProvider,
    ResponseAnalyzer,
    ResponseGenerator,
)
from app.rag.retrieval.retrieval_engine import BM25Index, QueryExpander, ResultReranker, RetrievalEngine
from app.services.analytics_service import AnalyticsService
from app.services.indexing_service import get_vector_store
from app.services.repository_service import RepositoryService
from app.utils.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class ChatService:
    """Handle AI chat queries with RAG pipeline."""

    @staticmethod
    async def send_query(
        db: AsyncSession,
        user_id: UUID,
        repository_id: UUID,
        query: str,
        conversation_id: Optional[UUID] = None,
        context_limit: int = 5,
    ) -> dict:
        await RepositoryService.verify_repository_access(db, repository_id, user_id)
        repo = await RepositoryService.get_repository_by_id(db, repository_id)

        if repo.indexing_status != "completed":
            raise ValidationException("Repository is not indexed yet. Please index first.")

        start = time.time()

        if conversation_id:
            conv_result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
            conversation = conv_result.scalars().first()
            if not conversation:
                raise NotFoundException("Conversation not found")
        else:
            conversation = Conversation(
                user_id=user_id,
                repository_id=repository_id,
                title=query[:100],
                llm_model=settings.OPENAI_MODEL,
                embedding_model=settings.EMBEDDING_MODEL,
            )
            db.add(conversation)
            await db.flush()

        embedding_model = GeminiEmbeddingModel(
            api_key=settings.GEMINI_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
        processor = EmbeddingProcessor(embedding_model)
        query_embedding = await processor.model.embed_text(query)

        vector_store = get_vector_store()
        bm25 = BM25Index.get_instance(str(repository_id))
        retrieval = RetrievalEngine(vector_store, bm25)

        expanded = QueryExpander.expand_query(query)
        all_results = []
        for q in expanded[:3]:
            results = await retrieval.hybrid_search(
                query_text=q,
                query_embedding=query_embedding,
                repository_id=str(repository_id),
                top_k=context_limit * 2,
            )
            all_results.extend(results)

        seen = set()
        unique_results = []
        for r in all_results:
            rid = r.get("id") or r.get("chunk_id")
            if rid not in seen:
                seen.add(rid)
                unique_results.append(r)

        reranker = ResultReranker()
        top_chunks = await reranker.rerank(query, unique_results, top_k=context_limit)

        context_chunks = []
        for chunk in top_chunks:
            meta = chunk.get("metadata", {})
            context_chunks.append({
                "snippet": chunk.get("content") or chunk.get("snippet", ""),
                "file_path": meta.get("file_path", ""),
                "entity_name": meta.get("entity_name", ""),
                "chunk_id": meta.get("chunk_id") or chunk.get("chunk_id"),
                "score": chunk.get("combined_score", chunk.get("similarity_score", 0)),
            })

        llm = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
        generator = ResponseGenerator(llm)

        # Primary generation attempt using configured Gemini model. On failures
        # (quota exhausted, auth errors, etc.) try OpenAI fallback if configured.
        try:
            response_text = await generator.generate_response(query, context_chunks)
        except Exception as e:
            logger.exception("Primary LLM generation failed: %s", str(e))

            # Try to detect quota/auth issues and fallback to OpenAI if available.
            fallback_tried = False
            try:
                if settings.OPENAI_API_KEY:
                    fallback_llm = OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
                    fallback_generator = ResponseGenerator(fallback_llm)
                    response_text = await fallback_generator.generate_response(query, context_chunks)
                    fallback_tried = True
                    logger.info("Fallback to OpenAI successful for chat query")
            except Exception as fe:
                logger.exception("Fallback OpenAI generation failed: %s", str(fe))

            if not fallback_tried:
                # Graceful user-facing message when generation is unavailable.
                response_text = (
                    "The AI generation service is temporarily unavailable. "
                    "Please try again later or contact an administrator."
                )

        avg_score = sum(c.get("score", 0) for c in context_chunks) / max(len(context_chunks), 1)
        confidence = ResponseAnalyzer.calculate_confidence_score(
            response_text, context_chunks, avg_score
        )

        elapsed_ms = int((time.time() - start) * 1000)

        message = Message(
            conversation_id=conversation.id,
            user_id=user_id,
            message_type="assistant",
            query_text=query,
            response_text=response_text,
            processing_time_ms=elapsed_ms,
            confidence_score=confidence,
        )
        db.add(message)
        await db.flush()

        citations = await ChatService._save_citations(db, message.id, context_chunks)
        conversation.message_count += 1
        conversation.last_message_at = message.created_at
        await db.commit()

        await AnalyticsService.track_event(
            db, user_id, "chat", "query_sent",
            {"repository_id": str(repository_id), "confidence": confidence},
            repository_id=repository_id,
            conversation_id=conversation.id,
        )

        return {
            "message_id": message.id,
            "conversation_id": conversation.id,
            "query": query,
            "response": response_text,
            "citations": citations,
            "confidence_score": confidence,
            "processing_time_ms": elapsed_ms,
            "tokens_used": {"query_chars": len(query), "response_chars": len(response_text)},
        }

    @staticmethod
    async def _save_citations(
        db: AsyncSession,
        message_id: UUID,
        context_chunks: List[dict],
    ) -> List[dict]:
        citations = []
        for i, chunk in enumerate(context_chunks):
            chunk_id = chunk.get("chunk_id")
            if not chunk_id:
                continue

            chunk_result = await db.execute(
                select(CodeChunk).where(CodeChunk.id == UUID(str(chunk_id)))
            )
            db_chunk = chunk_result.scalars().first()
            if not db_chunk:
                continue

            citation = Citation(
                message_id=message_id,
                code_chunk_id=db_chunk.id,
                file_id=db_chunk.file_id,
                citation_index=i + 1,
                citation_type="direct",
                relevance_score=chunk.get("score", 0),
                snippet_text=chunk.get("snippet", "")[:500],
                start_line=db_chunk.start_line_number,
                end_line=db_chunk.end_line_number,
            )
            db.add(citation)
            await db.flush()

            file_result = await db.execute(
                select(RepositoryFile).where(RepositoryFile.id == db_chunk.file_id)
            )
            db_file = file_result.scalars().first()

            citations.append({
                "id": citation.id,
                "file_path": db_file.file_path if db_file else chunk.get("file_path", ""),
                "snippet": citation.snippet_text,
                "start_line": citation.start_line,
                "end_line": citation.end_line,
                "relevance_score": citation.relevance_score or 0,
            })

        return citations

    @staticmethod
    async def get_conversations(
        db: AsyncSession,
        user_id: UUID,
        repository_id: Optional[UUID] = None,
    ) -> List[Conversation]:
        query = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )
        if repository_id:
            query = query.where(Conversation.repository_id == repository_id)
        query = query.order_by(desc(Conversation.last_message_at))
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> List[Message]:
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        if not conv_result.scalars().first():
            raise NotFoundException("Conversation not found")

        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> None:
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conversation = conv_result.scalars().first()
        if not conversation:
            raise NotFoundException("Conversation not found")

        conversation.deleted_at = datetime.utcnow()
        await db.commit()
