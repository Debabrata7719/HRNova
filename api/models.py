"""Pydantic Models for NovaHR API"""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    session_id: str
    role: str = "hr"  # "hr" or "employee" — no auth for now, just pass role
    employee_id: int = 0
    employee_name: str = ""


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
