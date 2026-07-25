from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas import ChatQueryRequest, ConversationCreate
from app.services.chat_service import ChatService
from app.utils.exceptions import create_response

router = APIRouter()


@router.post("")
async def send_chat_query(
    body: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a natural language query about a repository."""
    result = await ChatService.send_query(
        db=db,
        user_id=current_user.id,
        repository_id=body.repository_id,
        query=body.query,
        conversation_id=body.conversation_id,
        context_limit=body.context_limit or 5,
    )
    return create_response(success=True, status_code=200, data=result)


@router.get("/history")
async def get_chat_history(
    repository_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversation history."""
    conversations = await ChatService.get_conversations(
        db, current_user.id, repository_id
    )
    items = [
        {
            "id": str(c.id),
            "title": c.title,
            "repository_id": str(c.repository_id) if c.repository_id else None,
            "message_count": c.message_count,
            "created_at": c.created_at.isoformat(),
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
        }
        for c in conversations
    ]
    return create_response(success=True, status_code=200, data={"conversations": items})


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages in a conversation."""
    messages = await ChatService.get_conversation_messages(
        db, conversation_id, current_user.id
    )
    items = [
        {
            "id": str(m.id),
            "message_type": m.message_type,
            "query": m.query_text,
            "response": m.response_text,
            "confidence_score": m.confidence_score,
            "processing_time_ms": m.processing_time_ms,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
    return create_response(success=True, status_code=200, data={"messages": items})


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation."""
    await ChatService.delete_conversation(db, conversation_id, current_user.id)
    return create_response(success=True, status_code=200, message="Conversation deleted")
