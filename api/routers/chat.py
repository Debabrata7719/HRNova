"""Chat Router - Handles chat endpoints for NovaHR"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from api.models import ChatRequest, ChatResponse, SessionInfo
from api.dependencies.auth import get_current_user
from src.main_agent import run_main_agent
from typing import Dict

router = APIRouter()

# In-memory session store
sessions: Dict[str, dict] = {}


def get_initial_state(employee_id: int = 0, employee_name: str = "") -> dict:
    """
    Returns a fresh initial state for a new session.

    Args:
        employee_id: Employee ID from JWT token
        employee_name: Employee name from JWT token

    Returns:
        Initial state dictionary
    """
    return {
        "input": "",
        "intent": "",
        "step": "initial",
        "leave_data": {},
        "email_data": {},
        "schedule_data": {},
        "output": "",
        "employee_id": employee_id,
        "employee_name": employee_name,
        "schedule_title": "",
        "schedule_date": "",
        "schedule_time": "",
        "schedule_description": "",
        "leave_agent_memory": {},
        "email_agent_memory": {},
        "general_agent_memory": {},
        "query_agent_memory": {},
        "schedule_agent_memory": {},
        "session_summaries": {},
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    """
    Process a chat message and return the agent's response.
    Requires a valid JWT token in the Authorization header.

    Args:
        request: ChatRequest with message and session_id
        user: Decoded JWT payload (injected by get_current_user)

    Returns:
        ChatResponse with agent's response and session state

    Raises:
        HTTPException 401: If token is invalid
        HTTPException 500: If agent processing fails
    """
    try:
        # Extract user info from JWT token
        employee_id = user.get("user_id", 0)
        employee_name = user.get("name", "")
        role = user.get("role", "EMPLOYEE")

        # Get or create session
        if request.session_id not in sessions:
            sessions[request.session_id] = get_initial_state(
                employee_id=employee_id,
                employee_name=employee_name
            )

        # Get current state
        state = sessions[request.session_id]

        # Inject user message
        state["input"] = request.message

        # Run through agent pipeline
        state = run_main_agent(state)

        # Save updated state back to session
        sessions[request.session_id] = state

        return ChatResponse(
            response=state.get("output", ""),
            session_id=request.session_id,
            intent=state.get("intent", None),
            step=state.get("step", None)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent processing failed: {str(e)}"
        )


@router.get("/chat/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, user=Depends(get_current_user)):
    """
    Get information about a specific session.
    Requires a valid JWT token.

    Args:
        session_id: The session ID to query
        user: Decoded JWT payload (injected by get_current_user)

    Returns:
        SessionInfo with session state information
    """
    if session_id in sessions:
        state = sessions[session_id]
        return SessionInfo(
            session_id=session_id,
            intent=state.get("intent", None),
            step=state.get("step", None),
            exists=True
        )
    else:
        return SessionInfo(
            session_id=session_id,
            intent=None,
            step=None,
            exists=False
        )


@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str, user=Depends(get_current_user)):
    """
    Delete a session and clear its state.
    Requires a valid JWT token.

    Args:
        session_id: The session ID to delete
        user: Decoded JWT payload (injected by get_current_user)

    Returns:
        Success or not found message
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session cleared successfully"}
    else:
        return {"message": "Session not found"}


@router.get("/chat/sessions")
async def list_sessions(user=Depends(get_current_user)):
    """
    List all active sessions (for debugging/monitoring).
    Requires a valid JWT token.

    Returns:
        Dictionary with session count and session IDs
    """
    return {
        "total_sessions": len(sessions),
        "session_ids": list(sessions.keys())
    }
