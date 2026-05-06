"""NovaHR FastAPI Application"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from api.routers import chat, auth, leaves, memory
from api.models import HealthResponse
from apscheduler.schedulers.background import BackgroundScheduler
from src.utils.memory_store import get_memory_store
from src.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="NovaHR API",
    description="AI-Powered HR Assistant Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ==================== AUTOMATIC MEMORY CLEANUP ====================
def cleanup_old_memories_job():
    """Background job — runs daily at 2 AM to delete memories older than 30 days."""
    try:
        logger.info("[MEMORY CLEANUP] Starting automatic cleanup...")
        memory_store = get_memory_store()
        stats_before = memory_store.get_stats()
        memory_store.cleanup_old_memories(days=30)
        stats_after = memory_store.get_stats()
        deleted = stats_before["total_memories"] - stats_after["total_memories"]
        logger.info(
            "[MEMORY CLEANUP] Done — deleted %d memories (%d → %d)",
            deleted,
            stats_before["total_memories"],
            stats_after["total_memories"],
        )
    except Exception as e:
        logger.error("[MEMORY CLEANUP] Failed: %s", e)


# Initialize scheduler
scheduler = BackgroundScheduler()

# Schedule cleanup job to run daily at 2 AM
scheduler.add_job(
    cleanup_old_memories_job,
    trigger='cron',
    hour=2,
    minute=0,
    id='memory_cleanup',
    name='Clean up old memories (30+ days)',
    replace_existing=True
)

# Start scheduler
scheduler.start()
logger.info("[SCHEDULER] Automatic memory cleanup enabled (runs daily at 2 AM)")


@app.on_event("shutdown")
def shutdown_scheduler():
    """Shutdown scheduler when app stops"""
    scheduler.shutdown()
    logger.info("[SCHEDULER] Scheduler stopped")
# ==================== END AUTOMATIC CLEANUP ====================


def custom_openapi():
    """Custom OpenAPI schema with Bearer token authentication"""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add Bearer token security scheme
    if "components" not in schema:
        schema["components"] = {}
    
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Apply security globally to all endpoints
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

# CORS — allow all origins for now (tighten later when frontend domain is known)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(leaves.router, prefix="/api", tags=["Leaves"])
app.include_router(memory.router, prefix="/api", tags=["Memory"])


@app.get("/", response_model=HealthResponse)
def root():
    """
    Root endpoint - returns API status.
    
    Returns:
        HealthResponse with API status
    """
    return HealthResponse(
        status="ok",
        message="NovaHR API is running"
    )


@app.get("/health", response_model=HealthResponse)
def health():
    """
    Health check endpoint - verifies API is healthy.
    
    Returns:
        HealthResponse with health status
    """
    return HealthResponse(
        status="ok",
        message="NovaHR API is healthy"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
