"""Auth Router - Handles login and JWT token generation"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import bcrypt
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.auth import login
from api.dependencies.auth import get_current_user
from src.tools.db_connection import get_db

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


@router.post("/login")
def login_api(request: LoginRequest):
    """Authenticate user and return JWT token."""
    result = login(request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return {"token": result["token"], "user": result["user"]}


@router.put("/change-password")
def change_password(request: ChangePasswordRequest, user=Depends(get_current_user)):
    """
    Change password for the currently authenticated user.
    Any role can use this endpoint.

    Rules:
    - current_password must match the stored hash
    - new_password must be at least 6 characters
    - new_password and confirm_password must match
    """
    # Validate new password length
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 6 characters"
        )

    # Confirm passwords match
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirm password do not match"
        )

    user_id = user.get("user_id")
    db = get_db()

    # Fetch current hashed password from DB
    result = db.execute_query(
        "SELECT password FROM employees WHERE id = %s", (user_id,)
    )
    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    stored_hash = result[0]["password"]

    # Verify current password
    if not bcrypt.checkpw(
        request.current_password.encode("utf-8"),
        stored_hash.encode("utf-8")
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Hash new password and update
    new_hash = bcrypt.hashpw(
        request.new_password.encode("utf-8"),
        bcrypt.gensalt(rounds=10)
    ).decode("utf-8")

    db.execute_query(
        "UPDATE employees SET password = %s WHERE id = %s",
        (new_hash, user_id)
    )

    return {"message": "Password changed successfully"}
