from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime
import traceback

from app.core.config import settings
from app.core.database import init_db, close_db
from app.utils.exceptions import APIException, create_response
from app.api.v1.router import router as v1_router

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Codebase Understanding System",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.teamflow.ai"]
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Exception handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle API exceptions."""
    logger.error(f"API Exception: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_response(
            success=False,
            status_code=exc.status_code,
            message=exc.detail,
            error={"code": getattr(exc, "error_code", "UNKNOWN_ERROR")},
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_response(
            success=False,
            status_code=exc.status_code,
            message=exc.detail,
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content=create_response(
            success=False,
            status_code=422,
            message="Validation error",
            error={"details": exc.errors()},
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content=create_response(
            success=False,
            status_code=500,
            message="Internal server error",
        ),
    )


# Middleware for request logging
@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    """Log all requests."""
    import time
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Middleware error: {str(exc)}")
        raise
    
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {process_time:.2f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Lifespan events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        logger.warning("Continuing startup without a working database connection. Some features may be unavailable.")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application")
    
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Database cleanup failed: {str(e)}")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return create_response(
        success=True,
        status_code=200,
        message="Service is healthy",
        data={"status": "ok"},
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return create_response(
        success=True,
        status_code=200,
        message="Service is ready",
        data={"status": "ready"},
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return create_response(
        success=True,
        status_code=200,
        message=f"Welcome to {settings.APP_NAME}",
        data={
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/api/docs",
        },
    )


# API routes
app.include_router(v1_router, prefix=settings.API_V1_STR)

logger.info(f"{settings.APP_NAME} initialized successfully")
