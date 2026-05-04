"""Auth Router - Handles login and JWT token generation"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.auth import login

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str


@router.post("/login")
def login_api(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    Args:
        request: LoginRequest with email and password

    Returns:
        JWT token and user info on success

    Raises:
        HTTPException 401: If credentials are invalid
    """
    result = login(request.email, request.password)

    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])

    return {
        "token": result["token"],
        "user": result["user"]
    }
