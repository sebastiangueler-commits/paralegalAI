from celery import Celery
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "legal_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.bulk_import_tasks",
        "app.tasks.ai_training_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # 1 hour
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.bulk_import_tasks.*": {"queue": "import"},
    "app.tasks.ai_training_tasks.*": {"queue": "training"},
}

# Task annotations
celery_app.conf.task_annotations = {
    "*": {
        "rate_limit": "10/m",  # 10 tasks per minute
    }
}

# Error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    logger.info(f"Request: {self.request!r}")
    return "Debug task completed"

# Health check task
@celery_app.task(bind=True)
def health_check_task(self):
    """Health check task for monitoring."""
    try:
        from app.database import test_db_connection, test_redis_connection
        from app.ai_models import ai_models
        
        db_healthy = test_db_connection()
        redis_healthy = test_redis_connection()
        models_healthy = ai_models.models_loaded
        
        status = {
            "task_id": self.request.id,
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "ai_models": "healthy" if models_healthy else "unhealthy",
            "timestamp": self.request.utcnow().isoformat()
        }
        
        logger.info(f"Health check task completed: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Health check task failed: {e}")
        self.retry(countdown=60, max_retries=3)
        raise

# Task failure handling
@celery_app.task_failure.connect
def handle_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo):
    """Handle task failures."""
    logger.error(
        f"Task {task_id} failed: {exception}",
        extra={
            "task_id": task_id,
            "exception": str(exception),
            "args": args,
            "kwargs": kwargs,
            "traceback": traceback
        }
    )

# Task success handling
@celery_app.task_success.connect
def handle_task_success(sender, result):
    """Handle task success."""
    logger.info(f"Task {sender.request.id} completed successfully")

# Task retry handling
@celery_app.task_retry.connect
def handle_task_retry(sender, request, reason, einfo):
    """Handle task retries."""
    logger.warning(
        f"Task {request.id} retrying: {reason}",
        extra={
            "task_id": request.id,
            "reason": reason,
            "retry_count": request.retries
        }
    )