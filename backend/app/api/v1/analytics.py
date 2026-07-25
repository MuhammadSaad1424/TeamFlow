from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas import AnalyticsEventRequest
from app.services.analytics_service import AnalyticsService
from app.utils.exceptions import create_response

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics dashboard data."""
    data = await AnalyticsService.get_dashboard(db, current_user.id)
    return create_response(success=True, status_code=200, data=data)


@router.get("/usage")
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get usage statistics and rate limits."""
    data = await AnalyticsService.get_usage(db, current_user.id)
    return create_response(success=True, status_code=200, data=data)


@router.post("/events")
async def track_event(
    body: AnalyticsEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Track an analytics event."""
    await AnalyticsService.track_event(
        db,
        current_user.id,
        body.event_type,
        body.event_name,
        body.event_data,
    )
    return create_response(success=True, status_code=201, message="Event tracked")
