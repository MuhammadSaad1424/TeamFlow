from fastapi import APIRouter

from app.api.v1 import auth, repositories, chat, analytics, documentation, architecture

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(documentation.router, prefix="/documentation", tags=["Documentation"])
router.include_router(architecture.router, prefix="/architecture", tags=["Architecture"])
