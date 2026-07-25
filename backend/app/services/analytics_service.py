import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import AnalyticsEvent, Conversation, Message, Repository, User
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Analytics and usage tracking."""

    @staticmethod
    async def track_event(
        db: AsyncSession,
        user_id: UUID,
        event_type: str,
        event_name: str,
        event_data: Optional[dict] = None,
        repository_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
    ) -> None:
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            event_name=event_name,
            event_data=event_data,
            repository_id=repository_id,
            conversation_id=conversation_id,
        )
        db.add(event)
        await db.commit()

    @staticmethod
    async def get_dashboard(db: AsyncSession, user_id: UUID) -> dict:
        repo_count = await db.scalar(
            select(func.count(Repository.id)).where(
                Repository.user_id == user_id,
                Repository.deleted_at.is_(None),
            )
        )

        query_count = await db.scalar(
            select(func.count(Message.id)).where(
                Message.user_id == user_id,
                Message.message_type == "user",
            )
        )

        avg_time = await db.scalar(
            select(func.avg(Message.processing_time_ms)).where(
                Message.user_id == user_id,
                Message.processing_time_ms.isnot(None),
            )
        )

        avg_confidence = await db.scalar(
            select(func.avg(Message.confidence_score)).where(
                Message.user_id == user_id,
                Message.confidence_score.isnot(None),
            )
        )

        since = datetime.utcnow() - timedelta(days=7)
        daily = await db.execute(
            select(
                func.date(Message.created_at).label("day"),
                func.count(Message.id).label("count"),
            )
            .where(Message.user_id == user_id, Message.created_at >= since)
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at))
        )
        queries_by_day = [
            {"date": str(row.day), "count": row.count}
            for row in daily.all()
        ]

        recent = await db.execute(
            select(Message.query_text, func.count(Message.id).label("cnt"))
            .where(Message.user_id == user_id, Message.message_type == "user")
            .group_by(Message.query_text)
            .order_by(desc("cnt"))
            .limit(5)
        )
        top_questions = [
            {"question": row.query_text, "count": row.cnt}
            for row in recent.all()
        ]

        return {
            "total_queries": query_count or 0,
            "avg_query_time_ms": float(avg_time or 0),
            "avg_confidence_score": float(avg_confidence or 0),
            "total_repositories": repo_count or 0,
            "queries_by_day": queries_by_day,
            "top_questions": top_questions,
            "model_usage": {settings.OPENAI_MODEL: query_count or 0},
        }

    @staticmethod
    async def get_usage(db: AsyncSession, user_id: UUID) -> dict:
        tier_result = await db.execute(select(User.subscription_tier).where(User.id == user_id))
        tier = tier_result.scalar() or "free"
        limit = settings.RATE_LIMIT_QUERIES_PER_DAY.get(tier, 100)

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        used = await db.scalar(
            select(func.count(Message.id)).where(
                Message.user_id == user_id,
                Message.created_at >= today_start,
            )
        )

        return {
            "tier": tier,
            "daily_limit": limit,
            "used_today": used or 0,
            "remaining": max(0, limit - (used or 0)),
        }
