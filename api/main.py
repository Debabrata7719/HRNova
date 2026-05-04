"""NovaHR FastAPI Application"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from api.routers import chat, auth, leaves
from api.models import HealthResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="NovaHR API",
    description="AI-Powered HR Assistant Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add Bearer token security scheme
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
