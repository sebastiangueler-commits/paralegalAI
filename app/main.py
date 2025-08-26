from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1.api import api_router
from app.database import test_db_connection, test_redis_connection
from app.models import Base
from app.database import engine

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Legal AI Application...")
    
    # Test database connection
    if not test_db_connection():
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")
    
    # Test Redis connection
    if not test_redis_connection():
        logger.error("Failed to connect to Redis")
        raise RuntimeError("Redis connection failed")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    
    logger.info("Legal AI Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Legal AI Application...")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Legal AI System for Predictive Analysis and Document Generation",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        db_status = "healthy" if test_db_connection() else "unhealthy"
        
        # Check Redis
        redis_status = "healthy" if test_redis_connection() else "unhealthy"
        
        # Check AI models
        from app.ai_models import ai_models
        models_status = "healthy" if ai_models.models_loaded else "unhealthy"
        
        return {
            "status": "healthy" if all(s == "healthy" for s in [db_status, redis_status, models_status]) else "degraded",
            "timestamp": time.time(),
            "database": db_status,
            "redis": redis_status,
            "models": models_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with application information."""
    return {
        "message": "Legal AI Application",
        "version": settings.VERSION,
        "description": "Intelligent Legal AI System",
        "docs": "/docs",
        "health": "/health"
    }

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Legal AI Application is starting up...")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Legal AI Application is shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )