"""Pydantic Models for NovaHR API"""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoint - role/employee info comes from JWT token"""
    message: str
    session_id: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    session_id: str
    intent: Optional[str] = None
    step: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    intent: Optional[str] = None
    step: Optional[str] = None
    exists: bool


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    message: str
    version: str = "1.0.0"
